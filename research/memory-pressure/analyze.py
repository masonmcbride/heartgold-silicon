"""Summarize measured CSV/logs and emit standalone explanatory SVG charts."""
import argparse
import csv
import html
import json
from pathlib import Path
import re
import statistics


def percentile(values,p):
    v=sorted(values);i=(len(v)-1)*p;lo=int(i);hi=min(lo+1,len(v)-1)
    return v[lo]+(v[hi]-v[lo])*(i-lo)


def write_csv(path,rows):
    with path.open("w") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def chart(path,title,groups,unit):
    # Small explanatory distribution chart: individual observations and medians.
    # Data are also supplied as CSV; this is not a fitted model or causal plot.
    maximum=max(max(v) for v in groups.values())*1.12 or 1
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="360" viewBox="0 0 920 360">',
       '<rect width="920" height="360" fill="white"/>',
       '<g font-family="sans-serif" font-size="14" fill="#172536">',
       f'<text x="35" y="30" font-size="19">{html.escape(title)}</text>']
    for i in range(6):
        y=280-210*i/5;value=maximum*i/5
        s += [f'<path d="M85 {y} H890" stroke="#e1e5eb"/>',
              f'<text x="8" y="{y+5}">{value:.2f}</text>']
    for i,(name,values) in enumerate(groups.items()):
        x=175+i*210
        for j,v in enumerate(values):
            xx=x+(j-(len(values)-1)/2)*8;y=280-210*v/maximum
            s.append(f'<circle cx="{xx}" cy="{y}" r="4" fill="#146cb0"><title>{v:.6f} {unit}</title></circle>')
        y=280-210*statistics.median(values)/maximum
        s += [f'<path d="M{x-28} {y} H{x+28}" stroke="#d05626" stroke-width="3"/>',
              f'<text x="{x-65}" y="310">{html.escape(name)}</text>']
    s += [f'<text x="85" y="345">{html.escape(unit)}; blue = observations, orange = median. Small sample; no causal inference.</text>', '</g></svg>']
    path.write_text("\n".join(s))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("session",type=Path)
    args=p.parse_args();out=args.session
    trials=list(csv.DictReader((out/"trials.csv").open()))
    all_rows=[];latencies=[];resume=[];resources=[]
    for trial in trials:
        name,mode=trial["name"],trial["mode"]
        rows=list(csv.DictReader((out/f"{name}.csv").open()))
        for row in rows:
            row.update(name=name,mode=mode);all_rows.append(row)
        timings=[json.loads(m) for m in re.findall(r'HG_TIMING (\{[^\n]*?\})',(out/f"{name}.log").read_text())]
        cycle=0
        for t in timings:
            if t["phase"]=="original_constructor":cycle+=1
            latencies.append({"name":name,"mode":mode,"cycle":cycle,"phase":t["phase"],"ms":t["seconds"]*1000,
                "includes_idle":int(mode!="baseline" and cycle==1 and t["phase"]=="object_callbacks")})
        for index,row in enumerate(rows):
            if row["phase"]=="resume":
                end=next(r for r in rows[index+1:] if r["phase"]=="object_callbacks")
                begin=next(r for r in rows if r["phase"]=="idle_begin")
                resume.append({"name":name,"mode":mode,"resume_to_callbacks_ms":(int(end["continuous_ns"])-int(row["continuous_ns"]))/1e6,
                    "resume_excluding_sample_ms":(int(end["continuous_ns"])-int(row["continuous_ns"])-int(row.get("sample_duration_ns",0)))/1e6,
                    "idle_ms":(int(row["continuous_ns"])-int(begin["continuous_ns"]))/1e6,
                    "task_decompressions_delta":int(end["task_decompressions"])-int(begin["task_decompressions"]),
                    "task_faults_delta":int(end["task_faults"])-int(begin["task_faults"]),
                    "task_pageins_delta":int(end["task_pageins"])-int(begin["task_pageins"]),
                    "compressed_before_bytes":int(begin["compressed_bytes"]),"compressed_resume_bytes":int(row["compressed_bytes"]),
                    "system_compressions_delta":int(end["system_compressions"])-int(begin["system_compressions"]),
                    "system_decompressions_delta":int(end["system_decompressions"])-int(begin["system_decompressions"]),
                    "system_swapouts_delta":int(end["system_swapouts"])-int(begin["system_swapouts"])})
        text=(out/f"{name}.log").read_text()
        for label in ("HG_RESOURCES","HG_THUMB"):
            found=re.search(label+r' (\{[^\n]*?\})',text)
            assert found,label
            resources.append({"name":name,"mode":mode,"kind":label,"json":found[1]})
    summaries=[]
    for mode in ("baseline","idle","demand","released"):
        for cycle in (1,2):
            for phase in ("original_constructor","area_loader_frames","parent_load_cleanup"):
                values=[r["ms"] for r in latencies if r["mode"]==mode and r["cycle"]==cycle and r["phase"]==phase]
                summaries.append({"mode":mode,"cycle":cycle,"phase":phase,"n":len(values),"p50_ms":percentile(values,.5),
                    "p95_ms":percentile(values,.95),"p99_ms":percentile(values,.99),"max_ms":max(values)})
    write_csv(out/"samples.csv",all_rows);write_csv(out/"latencies.csv",latencies)
    write_csv(out/"latency-summary.csv",summaries);write_csv(out/"resume.csv",resume)
    write_csv(out/"resource-totals.csv",resources)
    groups={m:[r["resume_to_callbacks_ms"] for r in resume if r["mode"]==m] for m in ("idle","demand","released")}
    chart(out/"resume-latency.svg","Original callback probe after retained-resource idle",groups,"milliseconds")
    groups={m:[int(r["max_footprint_bytes"])/1048576 for r in trials if r["mode"]==m] for m in ("baseline","idle","demand","released")}
    chart(out/"peak-footprint.svg","Sampled engine-process footprint by condition",groups,"MiB")
    result={"trials":len(trials),"max_task_compressed_bytes":max(int(r["compressed_bytes"]) for r in all_rows),
        "max_task_decompressions":max(int(r["task_decompressions"]) for r in all_rows),
        "task_vm_counts":sorted(set(int(r["task_vm_count"]) for r in all_rows)),
        "task_vm_statuses":sorted(set(int(r["task_vm_status"]) for r in all_rows)),
        "sampled_resident_range_mib":[min(int(r["max_resident_bytes"]) for r in trials)/1048576,max(int(r["max_resident_bytes"]) for r in trials)/1048576],
        "sampled_peak_footprint_range_mib":[min(int(r["max_footprint_bytes"]) for r in trials)/1048576,max(int(r["max_footprint_bytes"]) for r in trials)/1048576],
        "resume_distributions":{m:{"n":len(v),"p50_ms":percentile(v,.5),"p95_ms":percentile(v,.95),"p99_ms":percentile(v,.99),"max_ms":max(v)} for m,v in
            {m:[r["resume_to_callbacks_ms"] for r in resume if r["mode"]==m] for m in ("idle","demand","released")}.items()}}
    (out/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
