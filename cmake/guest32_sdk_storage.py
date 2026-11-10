"""Recover actual existing SDK definitions using their production commands. MIT."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess


def recover(build,names,out):
    registry=json.loads((build/'native-overlays/provider-registry.json').read_text())
    providers={r['original_identity']:Path(r['artifact']) for r in registry['definitions']
               if r['image_owner']=='main' and r['abi_representation']=='native-arm64'
               and r['original_identity'] in names and '/libntr/' in r['artifact']}
    database=json.loads((build/'compile_commands.json').read_text())
    groups={};inputs={}
    for archive in sorted(set(providers.values())):
        inputs[str(archive)]=hashlib.sha256(archive.read_bytes()).hexdigest()
        r=subprocess.run(['nm','-A','-gU','-P',str(archive)],check=True,capture_output=True,text=True)
        for line in r.stdout.splitlines():
            m=re.match(r'^.*\[([^]]+)\]: _([^ ]+) ([A-Za-z]) ',line)
            if m and providers.get(m[2])==archive:
                groups.setdefault((archive,m[1]),[]).append(m[2])
    rows=[];out.mkdir(parents=True,exist_ok=True)
    for (archive,member),identities in groups.items():
        target=archive.stem.removeprefix('lib')
        matches=[]
        for row in database:
            args=row.get('arguments') or shlex.split(row['command'])
            if '-o' not in args:continue
            obj=args[args.index('-o')+1]
            if Path(obj).name==member and '/'+target+'.dir/' in '/'+obj:
                matches.append((row,args))
        if len(matches)!=1:raise ValueError('Nonunique actual SDK compilation owner: '+str((archive,member)))
        row,args=matches[0];source=Path(row['file']).resolve();inputs[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
        ir=out/(target+'-'+member+'.ll');command=[];i=0
        while i<len(args):
            arg=args[i]
            if arg in ('-o','-MF','-MT','-MQ'):i+=2;continue
            if arg not in ('-c','-MD','-MMD','-MP'):command.append(arg)
            i+=1
        command+=['-S','-emit-llvm','-o',str(ir.resolve())]
        result=subprocess.run(command,cwd=row['directory'],capture_output=True,text=True)
        (ir.with_suffix('.log')).write_text(result.stdout+result.stderr)
        if result.returncode:raise ValueError('Actual SDK storage frontend failed: '+str(source)+'\n'+result.stderr)
        rows.append(dict(ir=str(ir.resolve()),source=str(source),artifact=str(archive),member=member,identities=identities,command=command))
    (out/'providers.json').write_text(json.dumps(dict(providers=rows,inputs=inputs),indent=2))
    return rows,inputs
