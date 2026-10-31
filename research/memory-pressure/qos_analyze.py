"""Independent-process QoS analysis; blocked bootstrap, no p99 claims."""
import argparse
from collections import defaultdict
import csv
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import statistics


def write_csv(path,rows):
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def ratio_ci(pairs):
    # Each pair contains distinct processes from one counterbalanced block.
    # Resample whole blocks, retaining the matched comparison.
    logs=[math.log(a/b) for a,b in pairs]
    rng=random.Random(1729)
    boot=sorted(math.exp(statistics.mean(rng.choices(logs,k=len(logs)))) for _ in range(10000))
    return {'ratio':math.exp(statistics.mean(logs)),'ci95_low':boot[249],
            'ci95_high':boot[9749],'independent_process_pairs':len(pairs)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('session',type=Path)
    a=p.parse_args();out=a.session;trials=list(csv.DictReader((out/'trials.csv').open()))
    data=[];intervals=[];all_samples=[]
    for trial in trials:
        name=trial['name'];samples=list(csv.DictReader((out/f'{name}.csv').open()))
        assert all(x['qos_query_status']=='0' for x in samples)
        for s in samples:all_samples.append(s|{'name':name,'qos':trial['qos'],'demand':trial['demand']})
        cycles=defaultdict(int);previous=samples[0];resume=None
        for s in samples[1:]:
            phase=s['phase']
            if phase=='resume':resume=s
            if phase in ('idle_begin','idle_poll','resume'):continue
            cycles[phase]+=1
            begin=resume if phase=='object_callbacks' and cycles[phase]==1 else previous
            end=s
            row={'name':name,'block':int(trial['block']),'position':int(trial['position']),
                 'qos':trial['qos'],'demand':trial['demand'],'phase':phase,'cycle':cycles[phase]}
            for field,label,scale in [('continuous_ns','wall_ms',1e6),('process_cpu_ns','process_cpu_ms',1e6),('thread_cpu_ns','thread_cpu_ms',1e6),
                    ('voluntary_switches','voluntary_switches',1),('involuntary_switches','involuntary_switches',1),
                    ('task_faults','task_faults',1),('task_pageins','task_pageins',1),('task_decompressions','task_decompressions',1)]:
                row[label]=(int(end[field])-int(begin[field]))/scale
            row['wall_cpu_ratio']=row['wall_ms']/row['process_cpu_ms'] if row['process_cpu_ms'] else 0
            intervals.append(row);previous=s
        text=(out/f'{name}.log').read_text()
        thumb=json.loads(re.search(r'HG_THUMB (\{[^\n]*?\})',text)[1])
        resources=json.loads(re.search(r'HG_RESOURCES (\{[^\n]*?\})',text)[1])
        assert (resources['requests'],resources['loads'],resources['bytes'])==(2168,26,35245096)
        begin,end=samples[0],samples[-1]
        proc_ms=(int(end['process_cpu_ns'])-int(begin['process_cpu_ns']))/1e6
        first_parent=next(x for x in intervals if x['name']==name and x['phase']=='parent_load_cleanup' and x['cycle']==1)
        resumed=next(x for x in intervals if x['name']==name and x['phase']=='object_callbacks' and x['cycle']==1)
        data.append(trial|{'total_cpu_ms':proc_ms,'guest_steps':thumb['steps'],'guest_calls':thumb['calls'],
            'cpu_ns_per_guest_step':proc_ms*1e6/thumb['steps'],
            'parent_wall_ms':first_parent['wall_ms'],'parent_cpu_ms':first_parent['process_cpu_ms'],
            'parent_wall_cpu_ratio':first_parent['wall_cpu_ratio'],'parent_involuntary_switches':first_parent['involuntary_switches'],
            'resume_wall_ms':resumed['wall_ms'],'resume_cpu_ms':resumed['process_cpu_ms'],
            'peak_footprint_bytes':max(int(s['footprint_peak_bytes']) for s in samples),
            'max_compressed_bytes':max(int(s['compressed_bytes']) for s in samples),
            'max_compressed_lifetime_bytes':max(int(s['compressed_lifetime_bytes']) for s in samples),
            'max_decompressions':max(int(s['task_decompressions']) for s in samples),
            'max_thread_count':max(int(s['thread_count']) for s in samples)})
    groups=defaultdict(list)
    for d in data:groups[(d['qos'],d['demand'])].append(d)
    summary=[]
    for (qos,demand),rows in groups.items():
        for metric in ('parent_wall_ms','parent_cpu_ms','parent_wall_cpu_ratio','resume_wall_ms','resume_cpu_ms','cpu_ns_per_guest_step','parent_involuntary_switches'):
            values=[float(d[metric]) for d in rows]
            summary.append({'qos':qos,'demand':demand,'metric':metric,'n':len(values),
                'median':statistics.median(values),'min':min(values),'max':max(values)})
    comparisons={}
    for demand in ('none','held','active'):
        bg={d['block']:d for d in groups[('background',demand)]}
        fg={d['block']:d for d in groups[('initiated',demand)]}
        assert bg.keys()==fg.keys()
        for metric in ('parent_wall_ms','parent_cpu_ms','cpu_ns_per_guest_step','guest_steps'):
            comparisons[f'background_vs_initiated/{demand}/{metric}']=ratio_ci([(float(bg[b][metric]),float(fg[b][metric])) for b in bg])
    for qos in ('interactive','initiated','utility','background'):
        ref={d['block']:d for d in groups[(qos,'none')]}
        for demand in ('held','active'):
            alt={d['block']:d for d in groups[(qos,demand)]}
            for metric in ('parent_wall_ms','resume_wall_ms'):
                comparisons[f'{demand}_vs_none/{qos}/{metric}']=ratio_ci([(float(alt[b][metric]),float(ref[b][metric])) for b in ref])
    write_csv(out/'processes.csv',data);write_csv(out/'intervals.csv',intervals)
    write_csv(out/'samples.csv',all_samples);write_csv(out/'summary.csv',summary)
    result={'processes':len(data),'comparisons':comparisons,
        'max_process_compressed_bytes':max(d['max_compressed_bytes'] for d in data),
        'max_process_compressed_lifetime_bytes':max(d['max_compressed_lifetime_bytes'] for d in data),
        'max_process_decompressions':max(d['max_decompressions'] for d in data),
        'thread_counts':sorted(set(d['max_thread_count'] for d in data)),
        'thermal_states':sorted(set(int(s['thermal_state']) for s in all_samples)),
        'low_power_modes':sorted(set(int(s['low_power_mode']) for s in all_samples)),
        'snapshot_median_us':statistics.median(int(s['sample_duration_ns']) for s in all_samples)/1000,
        'snapshot_max_us':max(int(s['sample_duration_ns']) for s in all_samples)/1000,
        'power_sources':sorted(set(d['power_source'] for d in data)),
        'system_swapout_deltas':sorted(set(int(d['system_swapout_delta']) for d in data)),
        'inference':'No p99 estimate. Bootstrap CIs use independent process pairs clustered by counterbalanced block.'}
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    spec=importlib.util.spec_from_file_location('charts',Path(__file__).with_name('analyze.py'));charts=importlib.util.module_from_spec(spec);spec.loader.exec_module(charts)
    for demand in ('none','held','active'):
        chart_groups={q:[float(d['parent_wall_ms']) for d in groups[(q,demand)]] for q in ('interactive','initiated','utility','background')}
        charts.chart(out/f'parent-latency-{demand}.svg',f'Original partial FieldMap_Init integration interval — {demand}',chart_groups,'milliseconds')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
