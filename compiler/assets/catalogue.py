"""Developer-only generation of source constant descriptions and include routes.

No asset payloads, instruction streams, object files or converted images are stored.
Normal asset compilation consumes the declared catalogue; it never searches includes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from incremental import dependency_paths


def generate(game,ntr,build,clang,out):
    includes=[game,game/'include',game/'files',game/'asm',game/'asm/include',game/'lib/include',
              game/'lib/NitroSDK/include',ntr/'include',build/'generated/files',build/'generated/files/msgdata']
    profiles={};routes={};fingerprints={};header_scopes={}
    def identity(p):
        p=p.resolve()
        for tag,base in [('game',game),('ntr',ntr),('generated',build/'generated/files')]:
            if p.is_relative_to(base):return tag+':'+p.relative_to(base).as_posix()
        raise ValueError('Undeclared constant input: '+str(p))
    def resolve(name,parent):
        hits=[p for directory in [parent,*includes] if (p:=directory/name).is_file()]
        if not hits:raise ValueError('Missing original include: '+name)
        return hits[0].resolve()
    def track(p):
        key=identity(p)
        if key.startswith('generated:'):raise ValueError('Generated contents cannot enter source constant catalogue')
        fingerprints[key]=hashlib.sha256(p.read_bytes()).hexdigest()
        return key
    def local_header(p):
        key=track(p)
        definitions={}
        for line in p.read_text().splitlines():
            m=re.fullmatch(r'\s*#define\s+(\w+)\s+(.+?)\s*',line)
            if m:
                definitions[m[1]]=m[2].split('//',1)[0].strip()
        header_scopes[key]=definitions
    def asm_headers(relative,seen=None):
        seen=seen or set();p=game/relative
        if p in seen:return []
        seen.add(p);track(p);result=[]
        for name in re.findall(r'^\s*(?:#include|\.include)\s+"([^"]+)"',p.read_text(),re.M):
            target=resolve(name,p.parent)
            if target.suffix=='.inc':result+=asm_headers(target.relative_to(game).as_posix(),seen)
            else:result.append(target)
        return result
    selections={'field':['fielddata/script/scr_seq'], 'battle':['battledata/script/move_script','battledata/script/subscript']}
    for profile,archives in selections.items():
        headers=asm_headers('asm/macros/script.inc' if profile=='field' else 'asm/macros/btlcmd.inc')
        if profile=='field':
            for event in sorted((game/'files/fielddata/eventdata/zone_event').glob('*.json')):
                data=json.loads(event.read_text())
                if 'header' in data:
                    local_header(resolve(data['header'],event.parent))
        for archive in archives:
            for source in sorted((game/'files'/archive).glob('*.s')):
                bindings=[]
                for name in re.findall(r'^\s*#include\s+"([^"]+)"',source.read_text(),re.M):
                    target=resolve(name,source.parent);bindings.append(dict(name=name,path=identity(target)))
                    if target.is_relative_to(game/'files'):
                        local_header(target)
                    elif not target.is_relative_to(build):headers.append(target)
                if profile=='battle':bindings.append(dict(name='msg/msg_0197.h',path='generated:msgdata/msg/msg_0197.h'))
                routes[source.relative_to(game).as_posix()]=dict(profile=profile,headers=bindings)
        headers=list(dict.fromkeys(p for p in headers if not p.is_relative_to(build)))
        with tempfile.TemporaryDirectory(dir=build,prefix='asset constants ') as tmp:
            dep=Path(tmp)/'headers.d'
            cmd=[str(clang),'-E','-dM','-x','assembler-with-cpp','-DPM_ASM','-DSDK_ASM',
                 '-Werror=macro-redefined','-MD','-MF',str(dep),'-MT','constants']
            if profile=='battle':cmd+=['-D__ASM_PM_']
            for directory in includes:cmd+=['-I',str(directory)]
            text=''.join('#include '+json.dumps(str(p))+'\n' for p in headers)
            r=subprocess.run([*cmd,'-'],input=text,capture_output=True,text=True,check=True)
            for name in dependency_paths(dep.read_text()):
                if name!='-':track(Path(name))
            constants={}
            for line in r.stdout.splitlines():
                match=re.fullmatch(r'#define (\w+)(\([^)]*\))?\s*(.*)',line)
                if not match:raise ValueError('Unknown constant definition: '+line)
                name,params,body=match.groups()
                if name.startswith('__'):continue
                constants[name]=dict(params=None if params is None else [p.strip() for p in params[1:-1].split(',') if p.strip()],body=body)
            profiles[profile]=constants
    # Event headers introduce only original map/script definitions, already
    # represented by the field constant scope. Record their literal include routes.
    for source in sorted((game/'files/fielddata/eventdata/zone_event').glob('*.json')):
        data=json.loads(source.read_text());headers=[]
        if 'header' in data:
            target=resolve(data['header'],source.parent);headers.append(dict(name=data['header'],path=identity(target)))
            track(target)
        routes[source.relative_to(game).as_posix()]=dict(profile='field',headers=headers)
    track(game/'files/fielddata/eventdata/zone_event.json.txt')
    def enum_header(relative,enum):
        path=game/relative;track(path)
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',path.read_text(),flags=re.S)
        body=re.search(r'\benum\s+'+enum+r'\s*\{([^}]+)\}',text).group(1)
        previous=None
        for entry in body.split(','):
            entry=entry.strip()
            if not entry:continue
            name,separator,value=entry.partition('=');name=name.strip()
            if not re.fullmatch(r'\w+',name):raise ValueError('Unsupported source enum member: '+entry)
            value=value.strip() if separator else '0' if previous is None else previous+' + 1'
            profiles['field'][name]=dict(params=None,body=value);previous=name
    enum_header('include/filesystem_files_def.h','NarcId')
    enum_header('include/catching_show.h','PalParkEncounterType')
    for relative,pattern,kind,template in [
        ('files/data/resdat','*.json','resdat','files/data/resdat.json.txt'),
        ('files/data/mmodel/mmodel','*.json','mmodel','files/data/mmodel/mmodel.json.txt'),
        ('files/arc','ppark.json','ppark','files/arc/ppark.json.txt')]:
        track(game/template)
        for source in sorted((game/relative).glob(pattern)):
            routes[source.relative_to(game).as_posix()]=dict(profile='field',headers=[],format=kind)
    track(game/'include/sprite_resource.h');track(game/'include/sprite_resource_header.h')
    value=dict(version=1,provenance='Pinned source constants and include routes only; no compiled asset payloads.',
               inputs=fingerprints,profiles=profiles,routes=routes,header_scopes=header_scopes)
    out.write_text(json.dumps(value,separators=(',',':'))+'\n')
    print('Constant profiles:',{k:len(v) for k,v in profiles.items()},'routes:',len(routes),'source contracts:',len(fingerprints))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['game','ntr','build','clang','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();generate(a.game.resolve(),a.ntr.resolve(),a.build.resolve(),a.clang.resolve(),a.output.resolve())
