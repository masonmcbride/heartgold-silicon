"""Stable, content-validated frontend/description results within one build. MIT."""
import json
from pathlib import Path
import shutil
from contextlib import contextmanager
import fcntl
from incremental import run


@contextmanager
def backend_workspace(root):
    """One build-owned writer; publication never rebases compiler receipts."""
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    with (root/'writer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        yield root


def stable_overlay(root, entries):
    """Retain effective virtual bytes under paths unaffected by publication."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    roots = []
    for index, entry in enumerate(entries):
        target = root / 'virtual' / str(index) / Path(entry['name']).name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = Path(entry['external-contents']).read_bytes()
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
        roots.append(dict(entry, **{'external-contents': str(target)}))
    overlay = root / 'frontend.json'
    text = json.dumps(dict(version=0, roots=roots))
    if not overlay.exists() or overlay.read_text() != text:
        overlay.write_text(text)
    return overlay, {entry['name']: entry['external-contents'] for entry in roots}


def compile_frontend(source, cache, destination, clang, flags,
                     virtual_files, tools, inputs, resolved_paths=None):
    cache, destination = Path(cache), Path(destination)
    cache.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    ir = cache/'guest.ll'
    result = run([str(clang), *flags, '-S', '-emit-llvm', str(source), '-o', str(ir),
                  '-MD', '-MF', str(ir)+'.d'], [ir], inputs=[source], depfile=str(ir)+'.d',
                 virtual_files=virtual_files, tool_snapshot=tools[str(clang)], input_snapshot=inputs,
                 resolved_paths=resolved_paths)
    (destination/'frontend.log').write_text(result.stdout+result.stderr)
    if not result.returncode:
        shutil.copyfile(ir, destination/'guest.ll')
    return result


def discover(record, source, cache, destination, clang, lowerer, flags,
             virtual_files, tools, inputs, observe, resolved_paths=None):
    """Developer-only metadata generation; production uses declared ABI data."""
    record = dict(record)
    cache, destination = Path(cache), Path(destination)
    ir, desc = cache/'guest.ll', cache/'description.json'
    result = compile_frontend(source,cache,destination,clang,flags,virtual_files,tools,inputs,resolved_paths)
    observe(record['object'], 'frontend', result)
    record.update(frontend=not result.returncode, frontend_diagnostic=result.stderr)
    if result.returncode:
        return record
    result = run([str(lowerer), str(ir), str(cache/'unused.ll'), '--diagnose', str(desc)],
                 [desc], inputs=[ir], tool_snapshot=tools[str(lowerer)], input_snapshot=inputs)
    observe(record['object'], 'describe', result)
    if result.returncode:
        record['frontend_diagnostic'] += result.stderr
    else:
        record['description'] = json.loads(desc.read_text())
        shutil.copyfile(desc, destination/'description.json')
    return record


def prepare_lower(source_ir, cache, lowerer, abi, image, native, tools, inputs):
    from incremental import prepare
    return prepare(list(map(str,[lowerer,source_ir,cache/'native.ll','--abi',abi,
        '--native-ir',native,'--image',image,'--guest-externals','--prefix','guest32_'])),
        [cache/'native.ll'],inputs=[source_ir,abi,native,image],
        tool_snapshot=tools[str(lowerer)],input_snapshot=inputs)


def prepare_object(cache, clang, tools, inputs, extra_inputs=()):
    from incremental import prepare
    return prepare(list(map(str,[clang,'-O2','-c',cache/'native.ll','-o',cache/'native.o'])),
        [cache/'native.o'],inputs=[cache/'native.ll',*extra_inputs],
        tool_snapshot=tools[str(clang)],input_snapshot=inputs)


def publish_object(member, cache, destination, result, observe):
    observe(member,'codegen',result)
    (destination/'object.log').write_text(result.stdout+result.stderr)
    if not result.returncode:
        for file in ('abi.json','native.ll','native.o'):
            shutil.copyfile(cache/file,destination/file)
    return dict(member=member,compiled=not result.returncode,reason=result.stderr)


def compile_object(member, cache, destination, clang, tools, inputs, observe):
    from incremental import Pending
    result=prepare_object(cache,clang,tools,inputs)
    if isinstance(result,Pending):result=result.execute()
    return publish_object(member,cache,destination,result,observe)


def compile_objects(jobs, workspace, codegen, clang, tools, inputs, observe, workers):
    """One native Clang batch with independent per-module invalidation."""
    import subprocess
    from incremental import Pending
    codegen=Path(codegen).resolve()
    contract=codegen.with_name('codegen-inputs.json')
    declaration=json.loads(contract.read_text())
    if declaration.get('version')!=1 or len(declaration.get('libraries',[]))!=2:
        raise ValueError('Invalid declared native compiler library inputs')
    extra_inputs=[codegen,contract,*map(Path,declaration['libraries'])]
    pending=[];completed={}
    for job in jobs:
        result=prepare_object(job['cache'],clang,tools,inputs,extra_inputs)
        if isinstance(result,Pending):pending.append((job,result))
        else:completed[job['member']]=result
    if pending:
        request=workspace/'codegen-jobs.json';report=workspace/'codegen-report.json'
        request.write_text(json.dumps(dict(workers=workers,
            jobs=[operation.command for _,operation in pending]))+'\n')
        report.unlink(missing_ok=True)
        result=subprocess.run([str(codegen),str(request),str(report)],capture_output=True,text=True)
        (workspace/'codegen-batch.log').write_text(result.stdout+result.stderr)
        if result.returncode:
            raise ValueError('Declared native codegen batch failed:\n'+result.stdout+result.stderr)
        records=json.loads(report.read_text())['jobs']
        if (len(records)!=len(pending) or any(record['output']!=operation.command[5]
                for record,(_,operation) in zip(records,pending))):
            raise ValueError('Incomplete native codegen batch report')
        for record,(job,operation) in zip(records,pending):
            completed[job['member']]=operation.finish(
                subprocess.CompletedProcess(operation.command,0,'',record['stderr']),record['seconds'])
    return [publish_object(job['member'],job['cache'],job['destination'],
            completed[job['member']],observe) for job in jobs]


def compile_backend(member, source_ir, cache, destination, lowerer, clang,
                    abi, image, native, tools, inputs, observe):
    """Single-module entry retained for isolated fixtures and regressions."""
    from incremental import Pending
    cache,destination=Path(cache),Path(destination)
    cache.mkdir(parents=True,exist_ok=True)
    destination.mkdir(parents=True,exist_ok=True)
    result=prepare_lower(source_ir,cache,lowerer,abi,image,native,tools,inputs)
    if isinstance(result,Pending):result=result.execute()
    observe(member,'lower',result)
    (destination/'lower.log').write_text(result.stdout+result.stderr)
    if result.returncode:return dict(member=member,compiled=False,reason=result.stderr)
    return compile_object(member,cache,destination,clang,tools,inputs,observe)


def compile_backends(jobs, workspace, lowerer, clang, tools, inputs, observe, *, codegen, workers=4):
    """Finite lowering and native Clang batches with per-module receipts."""
    import subprocess
    import time
    from incremental import Pending
    started=time.perf_counter()
    pending=[]
    for job in jobs:
        result=prepare_lower(job['source_ir'],job['cache'],lowerer,job['abi'],
            job['image'],job['native'],tools,inputs)
        if isinstance(result,Pending):pending.append((job,result))
        else:
            observe(job['member'],'lower',result)
            (job['destination']/'lower.log').write_text(result.stdout+result.stderr)
    validation_seconds=time.perf_counter()-started
    batch_seconds=receipt_seconds=0.0
    if pending:
        request=workspace/'lower-jobs.json';report=workspace/'lower-report.json'
        request.write_text(json.dumps(dict(workers=workers,
            jobs=[operation.command for _,operation in pending]))+'\n')
        report.unlink(missing_ok=True)
        batch_started=time.perf_counter()
        result=subprocess.run([str(lowerer),'--lower-batch',str(request),str(report)],
            capture_output=True,text=True)
        batch_seconds=time.perf_counter()-batch_started
        (workspace/'lower-batch.log').write_text(result.stdout+result.stderr)
        if result.returncode:
            raise ValueError('Declared provider lowering batch failed:\n'+result.stdout+result.stderr)
        records=json.loads(report.read_text())['jobs']
        if (len(records)!=len(pending) or any(record['output']!=operation.command[2]
                for record,(_,operation) in zip(records,pending))):
            raise ValueError('Incomplete provider lowering batch report')
        receipt_started=time.perf_counter()
        for record,(job,operation) in zip(records,pending):
            result=operation.finish(subprocess.CompletedProcess(operation.command,0,record['stdout'],''),record['seconds'])
            observe(job['member'],'lower',result)
            (job['destination']/'lower.log').write_text(result.stdout)
        receipt_seconds=time.perf_counter()-receipt_started
    codegen_started=time.perf_counter()
    results=compile_objects(jobs,workspace,codegen,clang,tools,inputs,observe,workers)
    profile=dict(jobs=len(jobs),lowered=len(pending),reused=len(jobs)-len(pending),
        lower_validation_seconds=validation_seconds,lower_batch_seconds=batch_seconds,
        lower_receipt_seconds=receipt_seconds,codegen_and_publication_seconds=time.perf_counter()-codegen_started,
        total_seconds=time.perf_counter()-started)
    (workspace/'backend-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    return results
