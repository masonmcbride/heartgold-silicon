"""Serialize the original NitroFS inventory for the native CARD service.

This is a source resource image, not a retail ROM: no ARM program payloads or
retail file-ID equivalence are claimed. Files are never read from checkpoints.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct


def inventory(game, generated):
    text=(game/'filesystem.mk').read_text()
    declaration=re.search(r'^NITROFS_FILES := (.*?)(?=\n\n)',text,re.M|re.S)
    if not declaration:raise ValueError('Original NitroFS declaration missing')
    names=re.findall(r'files/([^\s\\]+)',declaration[1])
    aliases={}
    for original,numeric in re.findall(r'\$\(eval \$\(call arc_strip_name,files/([^,]+),files/([^\)]+)\)\)',text):
        original=original.replace('$(shortname)','gold').replace('$(buildname)','heartgold.us')
        if '$' in original:raise ValueError('Unknown original version expression: '+original)
        aliases[numeric]=original
    if len(set(names))!=len(names):raise ValueError('Duplicate original resource path')
    entries=[]
    for name in names:
        relative=aliases.get(name,name)
        original=game/'files'/name
        # Numeric aliases are produced by original archive recipes. Original
        # committed binaries keep their original bytes; no generated directory
        # scan or opportunistic fallback changes resource selection.
        source=(original if original.is_file() else game/'files'/relative
                if (game/'files'/relative).is_file() else generated/relative)
        entries.append(dict(path=name,source=str(source.resolve())))
    return entries


def filename_table(entries):
    nodes=[dict(path='',parent=0,files=[],children=[])]
    indices={'':0}
    for index,entry in enumerate(entries):
        path=PurePosixPath(entry['path'])
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid NitroFS path')
        parent=0
        for component in path.parts[:-1]:
            relative=str(PurePosixPath(nodes[parent]['path'])/component)
            if relative not in indices:
                ident=len(nodes);indices[relative]=ident
                nodes.append(dict(path=relative,parent=parent,files=[],children=[]))
                nodes[parent]['children'].append((component,ident))
            parent=indices[relative]
        nodes[parent]['files'].append((path.name,index))
    if len(nodes)>4096:raise ValueError('NitroFS directory limit exceeded')
    table=bytearray(8*len(nodes));ordered=[]
    def name_bytes(name):
        raw=name.encode('ascii')
        if not 0<len(raw)<128:raise ValueError('NitroFS name length')
        return raw
    for index,node in enumerate(nodes):
        struct.pack_into('<IHH',table,index*8,len(table),len(ordered),len(nodes) if index==0 else 0xf000|node['parent'])
        for name,member in node['files']:
            raw=name_bytes(name);table.extend(bytes([len(raw)])+raw);ordered.append(member)
        for name,child in node['children']:
            raw=name_bytes(name);table.extend(bytes([128|len(raw)])+raw+struct.pack('<H',0xf000|child))
        table.append(0)
    return bytes(table),ordered,len(nodes)


def crc16(data):
    value=0xffff
    for byte in data:
        value^=byte
        for _ in range(8):value=(value>>1)^(0xa001 if value&1 else 0)
    return value


def pack(entries,output,manifest):
    fnt,order,directories=filename_table(entries)
    fat_offset=(512+len(fnt)+3)&~3
    payload=(fat_offset+8*len(entries)+3)&~3
    records=[]
    # Read every required resource before publishing either output.
    for file_id,index in enumerate(order):
        entry=entries[index];source=Path(entry['source']);size=source.stat().st_size
        records.append(dict(**entry,manifest_index=index,file_id=file_id,size=size,rom_start=payload,rom_end=payload+size))
        payload=(payload+size+3)&~3
    header=bytearray(512);header[12:18]=b'ADAJ01'
    struct.pack_into('<IIII',header,0x40,512,len(fnt),fat_offset,len(entries)*8)
    struct.pack_into('<I',header,0x80,records[-1]['rom_end'] if records else payload)
    struct.pack_into('<H',header,0x15e,crc16(header[:0x15e]))
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix(output.suffix+'.tmp')
    try:
        with temporary.open('wb') as stream:
            stream.write(header);stream.write(fnt)
            stream.write(bytes(fat_offset-stream.tell()))
            for row in records:stream.write(struct.pack('<II',row['rom_start'],row['rom_end']))
            for row in records:
                stream.write(bytes(row['rom_start']-stream.tell()))
                digest=hashlib.sha256()
                with Path(row['source']).open('rb') as source:
                    for block in iter(lambda:source.read(1024*1024),b''):digest.update(block);stream.write(block)
                if stream.tell()!=row['rom_end']:raise ValueError('Resource changed during serialization')
                row['sha256']=digest.hexdigest()
        temporary.replace(output)
    finally:temporary.unlink(missing_ok=True)
    report=dict(schema='heartgold-source-cartridge-v1',retail_rom_equivalent=False,retail_file_ids_verified=False,
        image=str(output),image_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),image_bytes=output.stat().st_size,
        fnt_offset=512,fnt_size=len(fnt),fat_offset=fat_offset,fat_size=len(entries)*8,
        directory_count=directories,resource_count=len(entries),entries=sorted(records,key=lambda e:e['manifest_index']))
    manifest.write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--generated',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--plan',action='store_true',help='Print required source paths without reading generated resources')
    args=parser.parse_args()
    entries=inventory(args.game,args.generated)
    if args.plan:print(json.dumps(entries,indent=2))
    else:pack(entries,args.output,args.manifest)


if __name__=='__main__':main()
