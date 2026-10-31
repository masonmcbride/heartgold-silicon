"""Observe an existing original field constructor; all outputs in a binary directory."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import random
import select
import socket
import subprocess
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engine",required=True,type=Path)
    p.add_argument("--build",required=True,type=Path)
    p.add_argument("--out",default="research/memory-pressure/session")
    p.add_argument("--trials",type=int,default=5)
    p.add_argument("--idle-seconds",type=float,default=2)
    p.add_argument("--demand-mib",type=int,default=256)
    args=p.parse_args()
    assert 1<=args.trials<=30 and 0<=args.demand_mib<=2048 and 0<args.idle_seconds<=30
    build=args.build.resolve();out=(build/args.out).resolve()
    assert out.is_relative_to(build) and out!=build
    assert not out.exists(),"use a new result directory"
    out.mkdir(parents=True)
    engine=args.engine.resolve();observer=build/"memory-research/libhg_memory_observer.dylib"
    helper=build/"memory-research/hg_memory_demand"
    mx=engine.parent.parent
    def command(cmd):
        r=subprocess.run(cmd,capture_output=True,text=True)
        return {"exit":r.returncode,"stdout":r.stdout,"stderr":r.stderr}
    metadata={"date_local":time.strftime("%Y-%m-%d %H:%M:%S %z"),"engine":str(engine),
        "page_size":os.sysconf("SC_PAGE_SIZE"),
        "engine_sha256":digest(engine),"observer_sha256":digest(observer),"helper_sha256":digest(helper),
        "arguments":vars(args)|{"engine":str(engine),"build":str(build)},
        "sw_vers":command(["sw_vers"]),"uname":command(["uname","-a"]),
        "xcode":command(["xcodebuild","-version"]),"clang":command(["clang","--version"]),
        "hardware":command(["system_profiler","SPHardwareDataType"]),
        "mx_head":command(["git","-C",str(mx),"rev-parse","HEAD"]),
        "mx_status":command(["git","-C",str(mx),"status","--short"]),
        "swapusage":command(["sysctl","vm.swapusage"]),
        "vm_stat_before":command(["vm_stat"]),"source_provenance":{}}
    metadata["hardware"]["stdout"]="\n".join(line for line in metadata["hardware"]["stdout"].splitlines()
        if not any(key in line for key in ("Serial Number", "UUID", "UDID")))+"\n"
    # Record source identities, without assuming a prebuilt executable matches
    # every current source/generated file in this independently changing checkout.
    for relative in ["tests/test_original_field_constructor.c","src/compat/resources.c",
                     "src/compat/native_heap.c","src/compat/original_loader.c",
                     "build/generated/original_field_constructor_provenance.json",
                     "build/generated/original_field_parent_provenance.json"]:
        path=mx/relative
        if path.exists():metadata["source_provenance"][relative]={"sha256":digest(path),"mtime_ns":path.stat().st_mtime_ns}
    (out/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    def system_sample():
        r=subprocess.run([str(helper),"--sample"],capture_output=True,text=True,check=True)
        row=next(csv.DictReader(io.StringIO(r.stdout)))
        assert row["host_vm_status"]=="0"
        return row
    system=[];summary=[]
    def sample(label):
        r=system_sample();r["label"]=label;system.append(r);return r
    for repeat in range(args.trials):
        modes=["baseline","idle","demand","released"]
        random.Random(1729+repeat).shuffle(modes)
        for mode in modes:
            name=f"{repeat:02d}-{mode}";csvpath=out/f"{name}.csv"
            parent,child=socket.socketpair();parent.settimeout(20)
            env=os.environ.copy();env.update(HG_PROFILE_RESOURCES="1",HG_MEMORY_CSV=str(csvpath),
                DYLD_INSERT_LIBRARIES=str(observer))
            if mode!="baseline":
                env.update(HG_MEMORY_IDLE_PHASE="area_loader_frames",HG_MEMORY_CONTROL_FD=str(child.fileno()))
            initial=sample(name+":before");demand=None
            started=time.monotonic_ns()
            with (out/f"{name}.log").open("w") as log:
                process=subprocess.Popen([str(engine)],env=env,stdout=log,stderr=log,pass_fds=(child.fileno(),))
                child.close()
                try:
                    if mode!="baseline":
                        assert parent.recv(1)==b"R","engine did not reach retained-resource boundary"
                        sample(name+":idle_begin")
                        if mode in ("demand","released"):
                            demand=subprocess.Popen([str(helper),str(args.demand_mib)],stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,text=True)
                            ready,_,_=select.select([demand.stdout],[],[],15)
                            assert ready,"demand ramp timeout"
                            line=demand.stdout.readline().strip()
                            assert line==f"READY {args.demand_mib}",f"safety stop: {line}"
                            sample(name+":demand_ready")
                        deadline=time.monotonic()+args.idle_seconds
                        while time.monotonic()<deadline:
                            responsiveness=time.monotonic()
                            current=sample(name+":hold")
                            assert time.monotonic()-responsiveness<2,"monitor responsiveness: stop"
                            assert int(current["system_swapouts"])==int(initial["system_swapouts"]),"swap growth: stop"
                            assert demand is None or demand.poll() is None,"helper safety stop"
                            time.sleep(min(.2,max(0,deadline-time.monotonic())))
                        if mode=="released":
                            demand.terminate();_,diagnostic=demand.communicate(timeout=5)
                            (out/f"{name}.demand.log").write_text(diagnostic);demand=None
                            sample(name+":released");time.sleep(.25)
                        parent.sendall(b"G")
                    code=process.wait(timeout=20)
                    assert code==0,f"engine exit {code}: {name}"
                finally:
                    parent.close()
                    if process.poll() is None:process.terminate();process.wait(timeout=5)
                    if demand is not None:
                        if demand.poll() is None:demand.terminate()
                        _,diagnostic=demand.communicate(timeout=5)
                        (out/f"{name}.demand.log").write_text(diagnostic)
            final=sample(name+":after")
            text=(out/f"{name}.log").read_text()
            for marker in ["Original area Load complete: 59 models bound",
                           "Original InitialLoad and four Tick frames: 8 props, 260 land triangles",
                           "Main/Exit remain unexecuted"]:
                assert marker in text,f"missing original workload invariant: {marker}"
            rows=list(csv.DictReader(csvpath.open()))
            assert len(rows)>12 and all(r["task_vm_status"]=="0" for r in rows)
            assert [r["phase"] for r in rows].count("original_constructor")==2
            summary.append({"trial":repeat,"mode":mode,"name":name,"process_ms":(time.monotonic_ns()-started)/1e6,
                "system_swapout_delta":int(final["system_swapouts"])-int(initial["system_swapouts"]),
                "max_compressed_bytes":max(int(r["compressed_bytes"]) for r in rows),
                "max_resident_bytes":max(int(r["resident_bytes"]) for r in rows),
                "max_footprint_bytes":max(int(r["footprint_bytes"]) for r in rows)})
            print(name,summary[-1],flush=True)
            assert summary[-1]["system_swapout_delta"]==0,"swap growth: stop further trials"
    for filename,rows in [("system.csv",system),("trials.csv",summary)]:
        with (out/filename).open("w") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/"vm-stat-after.txt").write_text(command(["vm_stat"])["stdout"])
    print("RESULTS",out)


if __name__=="__main__":main()
