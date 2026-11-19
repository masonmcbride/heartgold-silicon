"""Recover actual existing SDK definitions using their production commands. MIT."""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'compiler/guest32'))
from incremental import dependency_paths


def recover(build,names,out):
    registry=json.loads((build/'native-overlays/provider-registry.json').read_text())
    providers={r['original_identity']:Path(r['artifact']) for r in registry['definitions']
               if r['image_owner']=='main' and r['abi_representation']=='native-arm64'
               and r['original_identity'] in names and '/libntr/' in r['artifact']}
    database=json.loads((build/'compile_commands.json').read_text())
    groups={};inputs={str(build/'compile_commands.json'):hashlib.sha256((build/'compile_commands.json').read_bytes()).hexdigest()}
    for archive in sorted(set(providers.values())):
        inputs[str(archive)]=hashlib.sha256(archive.read_bytes()).hexdigest()
        r=subprocess.run(['nm','-A','-gU','-P',str(archive)],check=True,capture_output=True,text=True)
        for line in r.stdout.splitlines():
            m=re.match(r'^.*\[([^]]+)\]: _([^ ]+) ([A-Za-z]) ',line)
            if m and providers.get(m[2])==archive:
                groups.setdefault((archive,m[1]),[]).append(m[2])
    rows=[];out.mkdir(parents=True,exist_ok=True)
    commands={}
    for row in database:
        args=row.get('arguments')
        obj=row.get('output')
        if obj is None:
            args=args or shlex.split(row['command'])
            if '-o' not in args:continue
            obj=args[args.index('-o')+1]
        for owner in {part[:-4] for part in Path(obj).parts if part.endswith('.dir')}:
            commands.setdefault((owner,Path(obj).name),[]).append((row,args))
    for (archive,member),identities in groups.items():
        target=archive.stem.removeprefix('lib')
        matches=commands.get((target,member),[])
        if len(matches)!=1:raise ValueError('Nonunique actual SDK compilation owner: '+str((archive,member)))
        row,args=matches[0];args=args or shlex.split(row['command'])
        actual=args[args.index('-o')+1] if '-o' in args else ''
        if Path(actual).name!=member or '/'+target+'.dir/' not in '/'+actual:
            raise ValueError('SDK command/output ownership differs: '+str((archive,member)))
        source=Path(row['file']).resolve();inputs[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
        ir=out/(target+'-'+member+'.bc');command=[];i=0
        while i<len(args):
            arg=args[i]
            if arg in ('-o','-MF','-MT','-MQ'):i+=2;continue
            if arg not in ('-c','-MD','-MMD','-MP'):command.append(arg)
            i+=1
        depfile=ir.with_suffix('.d')
        command+=['-c','-emit-llvm','-o',str(ir.resolve()),'-MD','-MF',str(depfile.resolve())]
        result=subprocess.run(command,cwd=row['directory'],capture_output=True,text=True)
        (ir.with_suffix('.log')).write_text(result.stdout+result.stderr)
        if result.returncode:raise ValueError('Actual SDK storage frontend failed: '+str(source)+'\n'+result.stderr)
        for dependency in [command[0],*dependency_paths(depfile.read_text())]:
            path=str((Path(row['directory'])/dependency).resolve())
            if path not in inputs:inputs[path]=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        rows.append(dict(ir=str(ir.resolve()),source=str(source),artifact=str(archive),member=member,identities=identities,command=command))
    (out/'providers.json').write_text(json.dumps(dict(providers=rows,inputs=inputs),indent=2))
    return rows,inputs
