"""Validate the explicit asset dependency DAG once; run its native producer."""
import argparse
import json
from pathlib import Path
import subprocess


def order(jobs):
    owners={}
    for index,job in enumerate(jobs):
        for output in job['outputs']:
            if output in owners:raise ValueError('Duplicate asset owner: '+output)
            owners[output]=index
    result=[];states={}
    def visit(index):
        state=states.get(index,0)
        if state==1:raise ValueError('Cyclic declared asset plan')
        if state==2:return
        states[index]=1
        for source in jobs[index]['inputs']:
            if source in owners:visit(owners[source])
        states[index]=2;result.append(jobs[index])
    for index in range(len(jobs)):visit(index)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True,type=Path);parser.add_argument('--tool',type=Path)
    parser.add_argument('--report',type=Path);parser.add_argument('--prepare',action='store_true')
    a=parser.parse_args();spec=json.loads(a.plan.read_text())
    if spec['mode']!='data':spec['jobs']=order(spec['jobs'])
    prepared=a.plan.with_suffix('.ordered.json')
    text=json.dumps(spec,separators=(',',':'))+'\n'
    if not prepared.exists() or prepared.read_text()!=text:prepared.write_text(text)
    if not a.prepare:
        subprocess.run([str(a.tool),str(prepared),str(a.report)],check=True)
        result=json.loads(a.report.read_text())
        print(f"Native assets: {result['jobs']} declared outputs, {result['seconds']:.3f}s")

if __name__=='__main__':main()
