"""Counter schema and helper bounds; actual engine invariants are checked by run.py."""
import csv
import io
import os
import subprocess
import sys

helper=sys.argv[1]
run=subprocess.run([helper,"--sample"],capture_output=True,text=True,check=True)
reader=csv.DictReader(io.StringIO(run.stdout));row=next(reader)
assert None not in row and None not in row.values()
assert row["task_vm_status"]=="0" and row["host_vm_status"]=="0"
assert int(row["continuous_ns"])>0 and int(row["sample_duration_ns"])>=0
assert int(row["resident_bytes"])>0 and int(row["footprint_bytes"])>0
assert int(row["compressed_bytes"])>=0 and int(row["task_decompressions"])>=0
assert int(row["process_cpu_ns"])>0 and int(row["thread_cpu_ns"])>0
assert row["qos_query_status"]=="0" and int(row["thread_count"])>=1
for invalid in ("4097","-1","not-a-size"):
    result=subprocess.run([helper,invalid],capture_output=True,text=True)
    assert result.returncode==2
env=os.environ.copy();env["HG_DEMAND_QOS"]="initiated"
child=subprocess.Popen([helper,"0"],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
    assert child.stdout.readline().strip()=="READY 0"
finally:
    child.terminate();_,diagnostic=child.communicate(timeout=5)
assert child.returncode==0 and "demand_ready" in diagnostic
data=next(csv.DictReader(io.StringIO(diagnostic)))
assert data["qos_requested"]=="25" and data["qos_self"]=="25"
timer=subprocess.run([helper,"--timer"],capture_output=True,text=True,check=True)
assert "continuous_timer_pair_median_ns" in timer.stdout
print("Counters, CPU clocks, verified requested QoS, bounds, helper release and timer calibration verified")
