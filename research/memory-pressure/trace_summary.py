"""Read Instruments-exported CPU labels and running slices for the target PID."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def summarize(toc,table):
    pid=ET.parse(toc).find('.//target/process').attrib['pid']
    root=ET.parse(table).getroot()
    ids={e.attrib['id']:e for e in root.iter() if 'id' in e.attrib}
    def resolve(e):return ids[e.attrib['ref']] if 'ref' in e.attrib else e
    totals=defaultdict(int);sequences=defaultdict(list)
    for row in root.iter('row'):
        c=list(row);process=resolve(c[4]);p=process.find('pid')
        if p is None or resolve(p).text!=pid or resolve(c[2]).text!='Running':continue
        core=resolve(c[1]);duration=int(resolve(c[3]).text)
        label=core.attrib.get('fmt','unknown');totals[label]+=duration
        thread=resolve(c[5]);tid=thread.find('tid')
        if tid is not None:sequences[resolve(tid).text].append((int(resolve(c[0]).text),core.text,label))
    total=sum(totals.values())
    main=max(sequences,key=lambda k:len(sequences[k]));seq=sorted(sequences[main])
    return {'pid':int(pid),'running_ns_by_instruments_cpu_label':dict(totals),
        'captured_running_ns':total,
        'efficiency_fraction':sum(v for k,v in totals.items() if '(E Core)' in k)/total,
        'performance_fraction':sum(v for k,v in totals.items() if '(P Core)' in k)/total,
        'main_thread_tid':main,'main_thread_running_slices':len(seq),
        'successive_main_thread_cpu_changes':sum(a[1]!=b[1] for a,b in zip(seq,seq[1:])),
        'successive_main_thread_core_type_changes':sum(('(E Core)' in a[2])!=('(E Core)' in b[2]) for a,b in zip(seq,seq[1:])),
        'note':'Separate instrumented trace, not a timing replicate; fractions refer to captured Running intervals, not total elapsed time.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('toc',type=Path);p.add_argument('cpu_xml',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=summarize(a.toc,a.cpu_xml);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
