"""Typed source-region compilation for original DWC and resident Wi-Fi. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from native_data_ir import parse, raw_layout
from native_assembly_data import emit_reviewed, read_object, validate_object
from native_image_graph import parse_manifest, ownership
from native_storage import Field, Record, compile_region

INPUTS = Path(__file__).with_name('dwc_native_inputs.json')
DATA = 'lib/NitroDWC/asm/dwc_lib_data.s'
RODATA = 'lib/NitroDWC/asm/dwc_lib_rodata.s'
WIFI = 'lib/asm/wifi_data.s'
CALLBACKS = ('BucketSetValue','BucketAdd','BucketSub','BucketMult','BucketDiv','BucketConcat','BucketAvg',
             'BucketIntOp','BucketDoubleOp','BucketStringOp','TeamBucketIntOp','TeamBucketDoubleOp',
             'TeamBucketStringOp','PlayerBucketIntOp','PlayerBucketDoubleOp','PlayerBucketStringOp')
MEASURE = {
    'SocketState': ('Ov00SocketState', ('lastError','hName','hAliases','hAddrType','hLength','hAddrList','addr','addrList')),
    'Ca': ('CpsRootCa', ('name','modulusLength','modulus','exponentLength','exponent')),
    'Key': ('KeyTable', ('keys',)),
    'Persist': ('PersistSocket', ('socket','port','key')),
    'PersistBlock': ('NativePersistBlock', tuple('callback'+str(i) for i in range(16))),
    'BucketGlobals': ('BucketGlobals', ('intValue','defaultSet','doubleValue')),
    'PersistWork': ('PersistWork', ('values',)),
    'SoclState': ('SoclState', ('lastIp','addressState','ctrlSocket','cpsConfig')),
    'Pool': ('SoclCommandPacketPool', ('queue',)),
    'SocketParam': ('SoclSocketParam', ()),
    'SslConfig': ('CpsSslConfig', ()),
    'CpsSocket': ('CpsSocket', ('boundRemoteIp','localPort','remotePort','remoteIp')),
    'Fragment': ('CpsFragment', ()),
    'CpsState': ('CpsState', ('alloc','free','netmask','gateway','hostIp','dns','random')),
    'Thread': ('OSThread', ()),
    'Login': ('LoginGlobal', ()),
    'Auth': ('AuthState', ('work','userId')),
    'AuthInfo': ('AuthWiFiInfo', ()),
    'NetCheck': ('NetCheckState', ('redirected','httpParams','authParams')),
}


def pin(game):
    for source, expected in json.loads(INPUTS.read_text()).items():
        if hashlib.sha256((game/source).read_bytes()).hexdigest() != expected:
            raise ValueError('Original data/consumer source drift: '+source)


def abi_source(game):
    pin(game)
    key = re.search(r'typedef struct KeyTable \{.*?\} KeyTable;',
                    (game/'lib/NitroDWC/src/ap_connect.c').read_text(), re.S)[0]
    s = '#include <stddef.h>\n#include <stdint.h>\n#include <cps/cps_ssl_internal.h>\n#include <dwc/persist_internal.h>\n#include <dwc/dwc_main_internal.h>\n#include <dwc/auth_internal.h>\n#include <nitrowifi/socl_internal.h>\n'+key+'\n'
    from native_sources import native_socket_state
    s += native_socket_state((game/'lib/NitroDWC/src/gs_platform.c').read_text())[1]+'\n'
    s += 'typedef struct NativePersistBlock { PersistSocket socket;\n'
    s += ''.join('__typeof__(&'+name+') callback'+str(i)+';\n' for i,name in enumerate(CALLBACKS))
    s += '} NativePersistBlock;\nconst uint32_t HG_DwcNativeLayout[] = {\n'
    for _, (ty, fields) in MEASURE.items():
        s += 'sizeof('+ty+'), _Alignof('+ty+'),'
        s += ''.join('offsetof('+ty+','+f+'),' for f in fields)+'\n'
    return s+'};\n'


def read_abi(path):
    data, sections, symbols = read_object(path)
    symbol = next(s for s in symbols if s['name']=='_HG_DwcNativeLayout')
    section = sections[symbol['section']-1]
    start = section['offset']+symbol['value']-section['address']
    count = sum(2+len(fields) for _,fields in MEASURE.values())
    values = iter(struct.unpack_from('<'+str(count)+'I',data,start))
    result = {}
    for name, (_,fields) in MEASURE.items():
        result[name] = dict(size=next(values), alignment=next(values),
                            fields={f:next(values) for f in fields})
    if result['Ca']['size']!=40 or result['Key']['size']!=32 or result['Persist']['size']!=16:
        raise ValueError('Incorrect native record stride')
    return result


def view(game, relative):
    blocks = parse(game/relative)
    raw, labels, refs = raw_layout(blocks)
    return blocks, raw, labels, refs


def make(game, abi):
    pin(game)
    owners = ownership(parse_manifest(game/'main.lsf'))
    result = {'OVY_0': [], 'main': []}
    reports, blocked = [], []
    roots, raw, labels, refs = view(game, DATA)
    source_roots = [refs[('.data',labels['gDwcRootCaList'][1]+4*i)][0] for i in range(12)]
    if len(set(source_roots)) != 12:
        raise ValueError('Root CA table order/identity drift')
    records = []
    def ptr_array(name, count, section='.data'):
        start=labels[name][1]
        fields=tuple(Field(4*i,8*i,4,'data',refs[(section,start+4*i)][0]) for i in range(count))
        return Record(start,4*count,8*count,8,fields,name)
    for name,count in [('gDwcRootCaList',12),('gDwcConnTestUrl',1),('gDwcMonthNames',12),
                       ('gDwcBase64Alphabet',1),('DWCi_AC_SsidKeyTable',4)]:
        records.append(ptr_array(name,count))
    for name in source_roots:
        start=labels[name][1]; fields=[]
        for i,field in enumerate(MEASURE['Ca'][1]):
            kind='data' if i%2==0 else 'scalar'
            fields.append(Field(i*4,abi['Ca']['fields'][field],4,kind,
                                refs[('.data',start+i*4)][0] if kind=='data' else ''))
        records.append(Record(start,20,abi['Ca']['size'],abi['Ca']['alignment'],tuple(fields),'CpsRootCa:'+name))
    start=labels['ov00_022198D8'][1]
    fields=[Field(0,abi['Persist']['fields']['socket'],4), Field(4,abi['Persist']['fields']['port'],4),
            Field(8,abi['Persist']['fields']['key'],4,'data',refs[('.data',start+8)][0])]
    for i,name in enumerate(CALLBACKS):
        if refs[('.data',start+12+4*i)] != (name,4):
            raise ValueError('Wrong callback target type/order')
        fields.append(Field(12+4*i,abi['PersistBlock']['fields']['callback'+str(i)],4,'function',name))
    records.append(Record(start,76,abi['PersistBlock']['size'],8,tuple(fields),
                          'PersistSocket followed by separate callback slots'))
    # Existing original-source providers retain their symbols and allocations.
    existing = {'sStr_0000','sStr_Empty','sStr_HttpsNasDevNintendowifiNetAc',
                'sStr_HttpsNasNintendowifiNetAc_4','sStr_HttpsNasTestNintendowifiNetAc_2'}
    exports={b.symbol for b in roots if b.public}-existing
    def region(relative,sec,lo,hi,typed,exports,owner):
        if owners[relative[:-2]+'.o'] != [owner]:
            raise ValueError('Original source owner conflict: '+relative)
        blocks,report=compile_region(game/relative,sec,lo,hi,typed,owner=owner,
                                     requested_owner=owner,exports=exports,function_targets=CALLBACKS)
        result[owner].extend(blocks);reports.append(report)
    # All scalar/certificate/string bytes through the start of the QR aggregate
    # are retained, including gaps. No pointer gaps are replaced with zeros.
    region(DATA,'.data',0,labels['current_rec'][1],records,exports,'OVY_0')
    # Original QR storage, widened only at verified pointer/record boundaries.
    current = labels['current_rec'][1]
    static = labels['static_qr2_rec'][1]
    keys = labels['qr2_registered_key_list'][1]

    assert static == current + 4, 'QR current/static adjacency drift'
    assert raw['.data'][static:static+4] == bytes([255])*4
    assert raw['.data'][static+4:static+272] == bytes(268)

    current_record = Record(
        current, 4, 8, 8,
        (Field(0,0,4,'data','static_qr2_rec'),),
        'QRRecord *'
    )

    static_fields = (
        Field(0,0,4,'scalar'),
        *(Field(i,i,4,'scalar') for i in range(4,272,4)),
    )
    static_record = Record(
        static, 272, 320, 8, tuple(static_fields), 'QRRecord'
    )

    assert raw['.data'][keys+120:keys+1016] == bytes(896)
    key_fields = tuple(
        Field(4*i,8*i,4,'data',refs[('.data',keys+4*i)][0])
        if i < 30 else Field(4*i,8*i,4,'null')
        for i in range(254)
    )
    key_record = Record(
        keys, 1016, 2040, 8, key_fields, 'char *[255]'
    )

    # These are independent original labels; admit their complete native
    # regions while leaving all other unknown QR/server data blocked.
    qr_records = {
        'current_rec': current_record,
        'static_qr2_rec': static_record,
        'qr2_registered_key_list': key_record,
    }

    # Later source strings are complete fixed-byte objects; unknown QR records
    # and pointer tables remain blocked rather than receiving raw zero storage.
    for i,b in enumerate(roots):
        sec,lo=labels[b.symbol]
        if sec!='.data' or lo<labels['current_rec'][1]: continue
        hi=labels[roots[i+1].symbol][1] if i+1<len(roots) else len(raw[sec])
        if b.symbol in qr_records:
            record = qr_records[b.symbol]
            assert lo == record.start, 'QR label location drift'
            assert hi >= lo + record.guest_size, 'QR region truncated'
            region(DATA,sec,lo,hi,(record,),exports,'OVY_0')
        elif b.symbol.startswith(('sStr_','sFmt_','sKey_')) and not any(s==sec and lo<=p<hi for s,p in refs):
            region(DATA,sec,lo,hi,(),{b.symbol},'OVY_0')
        else:
            blocked.append(dict(source=DATA,symbol=b.symbol,start=lo,end=hi,
                                reason='Unverified QR/server native aggregate'))
    rb,rr,rl,rrefs=view(game,RODATA)
    exp={b.symbol for b in rb if b.public}
    region(RODATA,'.rodata',0,rl['ov00_022160F0'][1],(),exp,'OVY_0')
    blocked.append(dict(source=RODATA,symbol='ov00_022160F0',start=176,end=195,
                        reason='No verified native consumer type for 19-byte pointer-bearing record'))
    sb=rl['sbSkippedKeys'][1]
    region(RODATA,'.rodata',195,len(rr['.rodata']),
           (Record(sb,8,16,8,tuple(Field(4*i,8*i,4,'data',rrefs[('.rodata',sb+4*i)][0]) for i in range(2)),'char *[2]'),),exp,'OVY_0')
    # Middleware has legal leading version-section alignment that the ordinary
    # storage parser intentionally rejects. Handle only this pinned grammar.
    metadata=(game/'asm/middleware.s').read_text()
    if owners['asm/middleware.o'] != ['main']:
        raise ValueError('Middleware owner drift')
    grammar=r'\.balign 4, 0\s+(_version_\w+):\s+\.asciz "([^"\n]+)"'
    entries=re.findall(grammar,metadata)
    if len(entries)!=7: raise ValueError('Middleware metadata grammar drift')
    for name,text in entries:
        if name=='_version_NINTENDO_DWC_LOBBY': continue # existing provider
        data=text.encode('ascii')+b'\0'
        result['main'].append(dict(symbol=name,public=True,section='__const',
                                  alignment=4,explicit_alignment=4,native_items=[('bytes',data)],bytes=data,pointers=[]))

    # Resident initialized data. Existing admitted constant definitions are
    # preserved; their bytes may occur in this backing span without re-export.
    from native_wifi_constants import selected as wifi_selected
    wb,wr,wl,wrefs=view(game,WIFI)
    existing_wifi,_=wifi_selected(game)
    wexp={b.symbol for b in wb if b.public}-{b['symbol'] for b in existing_wifi}
    # The first pointer is initialized to NULL, with an adjacent s32. The
    # explicit pointer type is provided by socl_internal.h, not inferred zeros.
    # Compile this pair separately below; remaining scalar bytes remain exact.
    lo=wl['gSoclUdpSocketParam'][1]
    ptr=wl['gCpsCertOids'][1]
    record=Record(ptr,24,48,8,tuple(Field(4*i,8*i,4,'data',wrefs[('.data',ptr+4*i)][0]) for i in range(6)), 'const char *[6]')
    region(WIFI,'.data',lo,len(wr['.data']),(record,),wexp,'main')
    region(WIFI,'.rodata',0,len(wr['.rodata']),(),wexp,'main')
    # gSoclConfig's null native pointer is represented by a typed zero object,
    # and _0211062C remains the neighboring signed scalar with native alignment.
    result['main'].append(dict(symbol='gSoclConfig',public=True,section='__data',alignment=8,
                               native_items=[('bytes',bytes(8))],bytes=bytes(8),pointers=[]))
    result['main'].append(dict(symbol='_0211062C',public=True,section='__data',alignment=1,
                               native_items=[('bytes',bytes(wr['.data'][4:8]))],bytes=bytes(wr['.data'][4:8]),pointers=[]))
    # Source-verified native BSS aggregates: aliases share a single allocation.
    def zero(name,size,aliases,source,guest_size):
        bs,br,bl,_=view(game,source);sec,start=bl[name]
        after=[p for s,p in bl.values() if s==sec and p>=start+guest_size]
        if min(after,default=len(br[sec]))!=start+guest_size:
            raise ValueError('Original BSS aggregate extent drift: '+name)
        original={n:p-start for n,(s,p) in bl.items() if s==sec and start<=p<start+guest_size}
        if set(original)!=set(aliases): raise ValueError('BSS aliases incomplete: '+name)
        position=0; blocks=[]
        for n,off in sorted(aliases.items(),key=lambda pair:pair[1]):
            if off<position or off>=size: raise ValueError('Alias offset mismatch')
            if blocks: blocks[-1]['native_items']=[('bytes',bytes(off-position))];blocks[-1]['bytes']=bytes(off-position)
            blocks.append(dict(symbol=n,public=True,section='__bss',alignment=1,
                               native_items=[],bytes=b'',pointers=[]));position=off
        blocks[-1]['native_items']=[('bytes',bytes(size-position))];blocks[-1]['bytes']=bytes(size-position)
        owner=owners[source[:-2]+'.o'][0]
        if owner not in result: raise ValueError('Unverified BSS owner')
        blocks[0]['alignment']=8; result[owner].extend(blocks)
        reports.append(dict(source=source,owner=owner,bss=name,original_size=guest_size,native_size=size,
                            original_aliases=original,native_aliases=aliases))
    a=abi['SoclState'];zero('gSoclState',a['size'],{'gSoclState':0,'gSoclLastIp':a['fields']['lastIp'],
        'gSoclAddressState':a['fields']['addressState'],'gSoclCtrlSocket':a['fields']['ctrlSocket'],
        'gSoclCpsConfig':a['fields']['cpsConfig']},WIFI,64)
    zero('gSoclCommandPackets',abi['Pool']['size'],{'gSoclCommandPackets':0,
         'gSoclCommandPacketQueue':abi['Pool']['fields']['queue']},WIFI,36)
    zero('gSoclUdpDropCount',8,{'gSoclUdpDropCount':0},WIFI,8)
    for n in ('gSoclSockets','gSoclTrash'): zero(n,8,{n:0},WIFI,4)
    wifi_bss='lib/asm/wifi_bss.s'
    zero('gCpsRstSocket',abi['CpsSocket']['size'],{'gCpsRstSocket':0},wifi_bss,100)
    zero('gCpsDhcpSocket',abi['CpsSocket']['size'],{'gCpsDhcpSocket':0,
         '_021D4720':abi['CpsSocket']['fields']['boundRemoteIp']},wifi_bss,100)
    zero('gCpsScavengerThread',abi['Thread']['size'],{'gCpsScavengerThread':0},wifi_bss,192)
    zero('gCpsFragments',8*abi['Fragment']['size'],{'gCpsFragments':0},wifi_bss,448)
    zero('gCpsDhcpSendBuffer',384,{'gCpsDhcpSendBuffer':0,'gCpsDhcpPacket':42},wifi_bss,384)
    for name,size in [('gCpsDhcpRecvBuffer',0x994),('gCpsTcpipStack',0x800),('gWcmRssiCount',4),('gWcmRssi',32)]:
        zero(name,size,{name:0},wifi_bss,size)
    gamespy='lib/NitroDWC/asm/dwc_gamespy_bss.s'
    socket=abi['SocketState']['fields']
    # Original +0 is the null alias pointer; +4 is lastError; +8 starts
    # hostent; +24 is IPv4 scratch; +44 is the two-pointer address list.
    # The next 16 original bytes precede the bucket scratch aggregate.
    bucket=socket['addrList']+2*8+16
    zero('ov00_0221B1AC',bucket+abi['BucketGlobals']['size'],
         {'ov00_0221B1AC':0,'ov00_0221B1B4':socket['hName'],
          'ov00_0221B1C4':socket['addr'],'ov00_0221B1D8':socket['addrList'],
          'ov00_0221B1F0':bucket,
          'ov00_0221B1F8':bucket+abi['BucketGlobals']['fields']['doubleValue']},gamespy,84)
    zero('gPersistWork',abi['PersistWork']['size'],
         {'gPersistWork':0,'ov00_0221B230':abi['PersistWork']['fields']['values']},gamespy,560)
    for name,size in [('GSIACHostname',64),('__GSIACGamename',64),('gDwcGameName',256),
                      ('gDwcSecretKey',256),('gti2ClosingSocket',4),('gti2AddressStringIndex',4),
                      ('gti2AddressStrings',44),('nnRecvBuffer',512),('num_local_ips',4),
                      ('local_ip_list',20),('qr2_hostname',64),('qr2_query_buffer',256)]:
        zero(name,size,{name:0},gamespy,size)
    zero('gDwcLogin',abi['Login']['size'],{'gDwcLogin':0},'lib/NitroDWC/asm/dwc_lib_bss.s',12)
    zero('gDwcAuthState',abi['Auth']['fields']['userId']+abi['AuthInfo']['size'],
         {'gDwcAuthState':0,'ov00_0221A69C':abi['Auth']['fields']['work'],
          'ov00_0221A6A0':abi['Auth']['fields']['userId']},RODATA,32)
    a=abi['NetCheck'];zero('gDwcNetCheckState',a['size'],
         {'gDwcNetCheckState':0,'ov00_0221A6BC':a['fields']['redirected'],
          'ov00_0221A6D0':a['fields']['httpParams'],'ov00_0221A6EC':a['fields']['authParams']},RODATA,124)
    zero('gDwcHttpTestServer',4,{'gDwcHttpTestServer':0},RODATA,4)
    zero('gDwcSvcLocWork',8,{'gDwcSvcLocWork':0},RODATA,4)
    return result,dict(regions=reports,blocked=blocked,root_ca_order=source_roots,
                       callbacks=list(CALLBACKS),native_abi=abi,
                       source_hashes=json.loads(INPUTS.read_text()))



QR_STORAGE_SYMBOLS = frozenset((
    "current_rec",
    "static_qr2_rec",
    "qr2_registered_key_list",
))


def qr_storage_blocks(result):
    blocks = [
        block for block in result["OVY_0"]
        if block["symbol"] in QR_STORAGE_SYMBOLS
    ]
    names = [block["symbol"] for block in blocks]
    if len(blocks) != 3 or set(names) != QR_STORAGE_SYMBOLS:
        raise ValueError(
            "QR-only admission requires exactly three original "
            "OVY_0 storage records; found " + repr(names)
        )
    if not all(block["public"] for block in blocks):
        raise ValueError("QR-only records must have public original identities")
    return blocks



BULK_STORAGE_MANIFEST = (
    Path(__file__).resolve().parent / "dwc_ovy0_bulk_symbols.json"
)


def bulk_storage_blocks(result):
    names = json.loads(BULK_STORAGE_MANIFEST.read_text())
    if len(names) != 214 or len(set(names)) != 214:
        raise ValueError("Bulk admission manifest must contain 214 unique symbols")

    wanted = set(names)
    selected = [
        block for block in result["OVY_0"]
        if block["symbol"] in wanted
    ]

    found = [block["symbol"] for block in selected]
    if len(found) != 214 or set(found) != wanted:
        raise ValueError(
            "Bulk admission does not match original OVY_0 records: "
            + repr(sorted(wanted - set(found)))
        )

    if not all(block["public"] for block in selected):
        raise ValueError("Bulk admission contains a private provider")

    qr = QR_STORAGE_SYMBOLS
    if wanted & qr:
        raise ValueError("Bulk admission overlaps QR-only storage")

    return selected



FRONTIER_STORAGE_MANIFEST = (
    Path(__file__).resolve().parent / "dwc_ovy0_frontier_symbols.json"
)


def frontier_storage_blocks(result):
    manifest = json.loads(FRONTIER_STORAGE_MANIFEST.read_text())
    if manifest.get("owner") != "OVY_0":
        raise ValueError("Frontier owner must be OVY_0")

    names = manifest["symbols"]
    expected = manifest["expected_count"]

    if expected != 632 or len(names) != expected or len(set(names)) != expected:
        raise ValueError("Invalid frontier manifest cardinality")

    wanted = set(names)
    bulk = set(json.loads(BULK_STORAGE_MANIFEST.read_text()))

    if wanted & (bulk | QR_STORAGE_SYMBOLS):
        raise ValueError("Frontier overlaps admitted storage")

    selected = [
        block for block in result["OVY_0"]
        if block["symbol"] in wanted
    ]
    found = [block["symbol"] for block in selected]

    if len(found) != expected or set(found) != wanted:
        raise ValueError(
            "Frontier does not match original storage: "
            + repr(sorted(wanted - set(found)))
        )

    if not all(block["public"] for block in selected):
        raise ValueError("Frontier contains private storage")

    return selected


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--abi-object',type=Path);p.add_argument('--validate',type=Path)
    p.add_argument('--owner',choices=['main','OVY_0','OVY_0_qr','OVY_0_bulk','OVY_0_frontier'])
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if not a.abi_object:
        text=abi_source(a.game);path=a.out/'abi.c'
        if not path.exists() or path.read_text()!=text:path.write_text(text)
        return
    result,report=make(a.game,read_abi(a.abi_object))
    if a.validate:
        if a.owner == 'OVY_0_qr':
            selected = qr_storage_blocks(result)
        elif a.owner == 'OVY_0_bulk':
            selected = bulk_storage_blocks(result)
        elif a.owner == 'OVY_0_frontier':
            selected = frontier_storage_blocks(result)
        else:
            selected = result[a.owner]
        report['validation']=validate_object(a.validate,selected)
        (a.out/(a.owner+'-validated.json')).write_text(json.dumps(report,indent=2)+'\n')
    else:
        for owner,blocks in result.items():
            text=emit_reviewed(blocks);path=a.out/(owner+'.S')
            if not path.exists() or path.read_text()!=text:path.write_text(text)
        qr_text = emit_reviewed(qr_storage_blocks(result))
        qr_path = a.out/'OVY_0_qr.S'
        if not qr_path.exists() or qr_path.read_text()!=qr_text:
            qr_path.write_text(qr_text)
        bulk_text = emit_reviewed(bulk_storage_blocks(result))
        bulk_path = a.out/'OVY_0_bulk.S'
        if not bulk_path.exists() or bulk_path.read_text()!=bulk_text:
            bulk_path.write_text(bulk_text)
        frontier_text = emit_reviewed(frontier_storage_blocks(result))
        frontier_path = a.out/'OVY_0_frontier.S'
        if not frontier_path.exists() or frontier_path.read_text()!=frontier_text:
            frontier_path.write_text(frontier_text)
        (a.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
