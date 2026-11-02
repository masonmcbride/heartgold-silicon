/* Research-only supported Mach counters. Failed/absent fields are -1. */
#ifndef HG_MEMORY_METRICS_H
#define HG_MEMORY_METRICS_H
#include <mach/mach.h>
#include <mach/mach_time.h>
#include <mach/task_info.h>
#include <mach/vm_statistics.h>
#include <malloc/malloc.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <pthread/qos.h>
#include <sys/resource.h>
#include <time.h>

#ifdef HG_MEMORY_PLATFORM
int hg_platform_thermal(void);
int hg_platform_low_power(void);
#endif

static uint64_t hg_memory_ns(void) {
    mach_timebase_info_data_t tb; mach_timebase_info(&tb);
    return (uint64_t)((__uint128_t)mach_continuous_time()*tb.numer/tb.denom);
}
static void hg_memory_sample(int fd,const char *phase) {
    uint64_t sample_start=hg_memory_ns();
    struct rusage usage={0};getrusage(RUSAGE_SELF,&usage);
    struct timespec process_cpu={0},thread_cpu={0};
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&process_cpu);
    clock_gettime(CLOCK_THREAD_CPUTIME_ID,&thread_cpu);
    qos_class_t requested=QOS_CLASS_UNSPECIFIED;int relative=0;
    int qos_status=pthread_get_qos_class_np(pthread_self(),&requested,&relative);
    thread_act_array_t threads=NULL;mach_msg_type_number_t thread_count=0;
    kern_return_t threads_status=task_threads(mach_task_self(),&threads,&thread_count);
    if(threads_status==KERN_SUCCESS){
        for(unsigned i=0;i<thread_count;i++)mach_port_deallocate(mach_task_self(),threads[i]);
        vm_deallocate(mach_task_self(),(vm_address_t)threads,thread_count*sizeof(*threads));
    }
    int thermal=-1,low_power=-1;
#ifdef HG_MEMORY_PLATFORM
    thermal=hg_platform_thermal();low_power=hg_platform_low_power();
#endif
    task_vm_info_data_t t={0}; mach_msg_type_number_t tc=TASK_VM_INFO_COUNT;
    kern_return_t tr=task_info(mach_task_self(),TASK_VM_INFO,(task_info_t)&t,&tc);
    task_events_info_data_t e={0}; mach_msg_type_number_t ec=TASK_EVENTS_INFO_COUNT;
    kern_return_t er=task_info(mach_task_self(),TASK_EVENTS_INFO,(task_info_t)&e,&ec);
    vm_statistics64_data_t v={0}; mach_msg_type_number_t vc=HOST_VM_INFO64_COUNT;
    mach_port_t host=mach_host_self();
    kern_return_t vr=host_statistics64(host,HOST_VM_INFO64,(host_info64_t)&v,&vc);
    mach_port_deallocate(mach_task_self(),host);
    malloc_statistics_t a={0}; malloc_zone_statistics(NULL,&a);
    uint64_t sample_duration=hg_memory_ns()-sample_start;
    char line[4096];
#define T(x) (tr==KERN_SUCCESS?(long long)t.x:-1LL)
#define V(x) (vr==KERN_SUCCESS?(long long)v.x:-1LL)
    int n=snprintf(line,sizeof(line),
        "%llu,%s,%d,%u,%d,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%zu,%zu,%llu,%llu,%llu,%ld,%ld,%d,%u,%u,%d,%u,%d,%d\n",
        (unsigned long long)sample_start,phase,tr,tc,vr,
        T(resident_size),T(resident_size_peak),
        tr==0&&tc>=TASK_VM_INFO_REV1_COUNT?(long long)t.phys_footprint:-1LL,
        tr==0&&tc>=TASK_VM_INFO_REV3_COUNT?(long long)t.ledger_phys_footprint_peak:-1LL,
        T(internal),T(external),T(compressed),T(compressed_peak),T(compressed_lifetime),
        tr==0&&tc>=TASK_VM_INFO_REV5_COUNT?(long long)t.decompressions:-1LL,
        er==0?(long long)e.faults:-1LL,er==0?(long long)e.pageins:-1LL,
        V(compressor_page_count),V(total_uncompressed_pages_in_compressor),
        V(compressions),V(decompressions),V(faults),V(pageins),V(pageouts),V(swapins),V(swapouts),
        (size_t)a.blocks_in_use,a.size_in_use,(unsigned long long)sample_duration,
        (unsigned long long)process_cpu.tv_sec*1000000000ULL+process_cpu.tv_nsec,
        (unsigned long long)thread_cpu.tv_sec*1000000000ULL+thread_cpu.tv_nsec,
        usage.ru_nvcsw,usage.ru_nivcsw,qos_status,(unsigned)requested,(unsigned)qos_class_self(),relative,
        threads_status==KERN_SUCCESS?thread_count:0,thermal,low_power);
#undef T
#undef V
    if(n>0 && n<(int)sizeof(line)) (void)write(fd,line,(size_t)n);
}
static const char hg_memory_csv_header[]=
    "continuous_ns,phase,task_vm_status,task_vm_count,host_vm_status,resident_bytes,resident_peak_bytes,footprint_bytes,footprint_peak_bytes,internal_bytes,external_bytes,compressed_bytes,compressed_peak_bytes,compressed_lifetime_bytes,task_decompressions,task_faults,task_pageins,system_compressor_pages,system_uncompressed_compressor_pages,system_compressions,system_decompressions,system_faults,system_pageins,system_pageouts,system_swapins,system_swapouts,malloc_blocks_in_use,malloc_bytes_in_use,sample_duration_ns,process_cpu_ns,thread_cpu_ns,voluntary_switches,involuntary_switches,qos_query_status,qos_requested,qos_self,qos_relative,thread_count,thermal_state,low_power_mode\n";
#endif
