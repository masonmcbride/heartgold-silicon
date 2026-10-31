"""Counterbalanced QoS × demand trials using the identical original constructor."""
import argparse
import csv
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import time

CLASSES={"interactive":33,"initiated":25,"utility":17,"background":9}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    return {"code":r.returncode,"stdout":r.stdout,"stderr":r.stderr}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build",type=Path,required=True);p.add_argument("--engine",type=Path,required=True)
    p.add_argument("--out",required=True);p.add_argument("--blocks",type=int,default=8)
    p.add_argument("--idle-seconds",type=float,default=.5);p.add_argument("--demand-mib",type=int,default=256)
    p.add_argument("--classes",default=",".join(CLASSES))
    args=p.parse_args();build=args.build.resolve();engine=args.engine.resolve();out=(build/args.out).resolve()
    assert out.is_relative_to(build) and not out.exists()
    assert 1<=args.blocks<=30 and .1<=args.idle_seconds<=10 and 1<=args.demand_mib<=2048
    classes=args.classes.split(",");assert all(q in CLASSES for q in classes)
    out.mkdir(parents=True)
    tools=build/"memory-research";observer=tools/"libhg_memory_observer.dylib";helper=tools/"hg_memory_demand";platform=tools/"hg_memory_platform"
    def diagnostic():return json.loads(subprocess.check_output([str(platform)],text=True))
    initial_platform=diagnostic()
    metadata={"date":time.strftime("%Y-%m-%d %H:%M:%S %z"),"engine":str(engine),"engine_sha256":sha(engine),
        "observer_sha256":sha(observer),"helper_sha256":sha(helper),"platform_sha256":sha(platform),
        "arguments":vars(args)|{"build":str(build),"engine":str(engine)},"initial_platform":initial_platform,
        "sw_vers":command(["sw_vers"]),"xcode":command(["xcodebuild","-version"]),
        "sdk":command(["xcrun","--show-sdk-version"]),"power_modes":command(["pmset","-g","custom"]),
        "timer":command([str(helper),"--timer"]),"helper_qos":"initiated",
        "qos_note":"pthread getters verify requested class; overrides and P/E residency are not observable here",
        "source_provenance":{}}
    for path in [Path(__file__),Path(__file__).parents[2]/"hardware_drivers/memory_observer.c",
                 Path(__file__).parents[2]/"hardware_drivers/memory_metrics.h",
                 Path(__file__).parents[2]/"hardware_drivers/memory_demand.c"]:
        metadata["source_provenance"][str(path.resolve())]=sha(path)
    (out/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    def system():
        r=subprocess.check_output([str(helper),"--sample"],text=True)
        row=next(csv.DictReader(io.StringIO(r)));assert row["host_vm_status"]=="0";return row
    cells=list(itertools.product(classes,["none","held","active"]))
    # Rotated/reversed blocks balance neighboring conditions and position. Each
    # independent process has exactly two existing lifecycle cycles, not repeats
    # inserted into an original engine loop.
    summaries=[]
    for block in range(args.blocks):
        offset=(block*5)%len(cells);order=cells[offset:]+cells[:offset]
        if block%2:order=list(reversed(order))
        for position,(qos,demand_mode) in enumerate(order):
            name=f"b{block:02d}-p{position:02d}-{qos}-{demand_mode}"
            before=diagnostic();assert before["thermal_state"]==0 and before["low_power_mode"]==0,"environment changed: stop"
            first=system();parent,child=socket.socketpair();parent.settimeout(30)
            env=os.environ.copy();env.update(HG_PROFILE_RESOURCES="1",HG_MEMORY_CSV=str(out/f"{name}.csv"),
                DYLD_INSERT_LIBRARIES=str(observer),HG_MEMORY_QOS=qos,
                HG_MEMORY_IDLE_PHASE="area_loader_frames",HG_MEMORY_CONTROL_FD=str(child.fileno()))
            helper_process=None
            with (out/f"{name}.log").open("w") as log:
                process=subprocess.Popen([str(engine)],env=env,stdout=log,stderr=log,pass_fds=(child.fileno(),));child.close()
                try:
                    assert parent.recv(1)==b"R","missing retained original resource boundary"
                    if demand_mode!="none":
                        henv=os.environ.copy();henv["HG_DEMAND_QOS"]="initiated"
                        hcmd=[str(helper),str(args.demand_mib)]+(["--active"] if demand_mode=="active" else [])
                        helper_process=subprocess.Popen(hcmd,env=henv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                        ready,_,_=select.select([helper_process.stdout],[],[],20);assert ready,"helper timeout"
                        assert helper_process.stdout.readline().strip()==f"READY {args.demand_mib}","helper safety stop"
                    limit=time.monotonic()+args.idle_seconds
                    while time.monotonic()<limit:
                        start=time.monotonic();sample=system()
                        assert time.monotonic()-start<2,"responsiveness stop"
                        assert sample["system_swapouts"]==first["system_swapouts"],"swap-out safety stop"
                        assert helper_process is None or helper_process.poll() is None,"helper exited: safety stop"
                        time.sleep(min(.1,max(0,limit-time.monotonic())))
                    parent.sendall(b"G");assert process.wait(timeout=40)==0,"engine assertion or policy failure"
                finally:
                    parent.close()
                    if process.poll() is None:process.terminate();process.wait(timeout=5)
                    if helper_process is not None:
                        if helper_process.poll() is None:helper_process.terminate()
                        _,hlog=helper_process.communicate(timeout=5);(out/f"{name}.helper.log").write_text(hlog)
            last=system();after=diagnostic()
            rows=list(csv.DictReader((out/f"{name}.csv").open()))
            assert all(int(r["qos_requested"])==CLASSES[qos] and int(r["qos_self"])==CLASSES[qos] and r["qos_query_status"]=="0" for r in rows)
            assert all(r["thermal_state"]=="0" and r["low_power_mode"]=="0" for r in rows)
            assert before["power_source"]==after["power_source"]==initial_platform["power_source"],"power-source change: stop"
            assert after["thermal_state"]==0 and after["low_power_mode"]==0
            text=(out/f"{name}.log").read_text()
            for invariant in ["Original area Load complete: 59 models bound","Original InitialLoad and four Tick frames: 8 props, 260 land triangles","Main/Exit remain unexecuted"]:
                assert invariant in text,invariant
            assert len([r for r in rows if r["phase"]=="original_constructor"])==2
            record={"name":name,"block":block,"position":position,"qos":qos,"demand":demand_mode,
                "power_source":after["power_source"],"thermal_state":after["thermal_state"],
                "system_swapout_delta":int(last["system_swapouts"])-int(first["system_swapouts"])}
            summaries.append(record)
            with (out/"trials.csv").open("w") as f:
                w=csv.DictWriter(f,fieldnames=list(record));w.writeheader();w.writerows(summaries)
            (out/f"{name}.environment.json").write_text(json.dumps({"before":before,"after":after,"system_before":first,"system_after":last},indent=2)+"\n")
            print(name,"ok",flush=True)
            assert record["system_swapout_delta"]==0
    print("RESULTS",out)


if __name__=="__main__":main()
