/* Separate bounded external demand. Never allocates inside the engine. */
#include "memory_metrics.h"
#include <dispatch/dispatch.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

_Static_assert(ATOMIC_INT_LOCK_FREE==2,"signal-safe stop flag");
static atomic_int stop;
static dispatch_source_t pressure;
static void pressure_event(void *unused) {
    (void)unused;unsigned long flags=dispatch_source_get_data(pressure);
    fprintf(stderr,"memory_pressure_flags=%lu\n",flags);
    if(flags&(DISPATCH_MEMORYPRESSURE_WARN|DISPATCH_MEMORYPRESSURE_CRITICAL))stop=1;
}
static void signal_stop(int sig){(void)sig;stop=1;}
static int compare_u64(const void *a,const void *b){uint64_t x=*(const uint64_t *)a,y=*(const uint64_t *)b;return (x>y)-(x<y);}
int main(int argc,char **argv) {
    if(argc==2&&!strcmp(argv[1],"--timer")){
        uint64_t times[10001];
        for(unsigned i=0;i<10001;i++){uint64_t begin=hg_memory_ns();times[i]=hg_memory_ns()-begin;}
        qsort(times,10001,sizeof(*times),compare_u64);
        printf("{\"continuous_timer_pair_median_ns\":%llu,\"p99_ns\":%llu,\"minimum_ns\":%llu}\n",(unsigned long long)times[5000],(unsigned long long)times[9900],(unsigned long long)times[0]);return 0;
    }
    if(argc==2&&!strcmp(argv[1],"--sample")){
        write(1,hg_memory_csv_header,sizeof(hg_memory_csv_header)-1);
        hg_memory_sample(1,"system_sample");return 0;
    }
    int active=argc==3&&!strcmp(argv[2],"--active");
    if(argc!=2&&!active){fprintf(stderr,"usage: hg_memory_demand MiB (0..4096) [--active] | --sample\n");return 2;}
    const char *q=getenv("HG_DEMAND_QOS");
    if(q&&pthread_set_qos_class_self_np(!strcmp(q,"initiated")?QOS_CLASS_USER_INITIATED:QOS_CLASS_BACKGROUND,0))return 6;
    char *end;unsigned long mib=strtoul(argv[1],&end,10);
    if(!*argv[1]||*end||mib>4096)return 2;
    signal(SIGTERM,signal_stop);signal(SIGINT,signal_stop);
    pressure=dispatch_source_create(DISPATCH_SOURCE_TYPE_MEMORYPRESSURE,0,
        DISPATCH_MEMORYPRESSURE_NORMAL|DISPATCH_MEMORYPRESSURE_WARN|DISPATCH_MEMORYPRESSURE_CRITICAL,
        dispatch_get_global_queue(QOS_CLASS_UTILITY,0));
    if(!pressure)return 3;
    dispatch_source_set_event_handler_f(pressure,pressure_event);dispatch_resume(pressure);
    vm_statistics64_data_t initial={0};mach_msg_type_number_t count=HOST_VM_INFO64_COUNT;
    mach_port_t host=mach_host_self();
    if(host_statistics64(host,HOST_VM_INFO64,(host_info64_t)&initial,&count)!=KERN_SUCCESS)return 4;
    size_t bytes=(size_t)mib*1024*1024;
    unsigned char *p=bytes?mmap(NULL,bytes,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0):NULL;
    if(bytes&&p==MAP_FAILED)return 5;
    /* Touch all words with nonconstant deterministic data, in 64 MiB steps.
     * There is no repeated streaming loop or attempt to force compression. */
    uint64_t state=0x9e3779b97f4a7c15ULL;
    for(size_t base=0;base<bytes&&!stop;base+=64*1024*1024) {
        size_t finish=base+64*1024*1024;if(finish>bytes)finish=bytes;
        for(size_t i=base;i<finish;i+=8){state^=state<<13;state^=state>>7;state^=state<<17;memcpy(p+i,&state,8);}
        vm_statistics64_data_t v={0};count=HOST_VM_INFO64_COUNT;
        if(host_statistics64(host,HOST_VM_INFO64,(host_info64_t)&v,&count)!=KERN_SUCCESS||
            v.swapouts>initial.swapouts)stop=1;
        usleep(20000);
    }
    (void)write(2,hg_memory_csv_header,sizeof(hg_memory_csv_header)-1);
    hg_memory_sample(2,"demand_ready");
    printf("%s %lu\n",stop?"STOP":"READY",mib);fflush(stdout);
    uint64_t passes=0;
    while(!stop) {
        if(active&&bytes){
            volatile uint64_t *words=(volatile uint64_t *)p;
            for(size_t base=0;base<bytes/8&&!stop;base+=512*1024){
                size_t finish=base+512*1024;if(finish>bytes/8)finish=bytes/8;
                for(size_t i=base;i<finish;i++)words[i]=words[i]+1;
            }
            passes++;
        }else usleep(50000);
        vm_statistics64_data_t v={0};count=HOST_VM_INFO64_COUNT;
        if(host_statistics64(host,HOST_VM_INFO64,(host_info64_t)&v,&count)!=KERN_SUCCESS||
            v.swapouts>initial.swapouts)stop=1;
    }
    fprintf(stderr,"traffic_passes=%llu active=%d; passes are not measured DRAM bytes\n",(unsigned long long)passes,active);
    if(bytes)munmap(p,bytes);
    mach_port_deallocate(mach_task_self(),host);return 0;
}
