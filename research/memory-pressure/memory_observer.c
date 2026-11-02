/* Opt-in dyld observer for existing HG_TIMING boundaries, not a game import. */
#include "memory_metrics.h"
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/select.h>

static int output=-1, control=-1, idle_done;
static const char *idle_phase;
static __thread int observing;
__attribute__((constructor)) static void memory_start(void) {
    const char *path=getenv("HG_MEMORY_CSV");
    if(!path)return;
    const char *q=getenv("HG_MEMORY_QOS");
    if(q){
        qos_class_t cls=!strcmp(q,"interactive")?QOS_CLASS_USER_INTERACTIVE:
            !strcmp(q,"initiated")?QOS_CLASS_USER_INITIATED:
            !strcmp(q,"utility")?QOS_CLASS_UTILITY:
            !strcmp(q,"background")?QOS_CLASS_BACKGROUND:QOS_CLASS_UNSPECIFIED;
        if(cls==QOS_CLASS_UNSPECIFIED||pthread_set_qos_class_self_np(cls,0))_exit(123);
    }
    output=open(path,O_WRONLY|O_CREAT|O_TRUNC,0600);
    if(output<0)_exit(120);
    (void)write(output,hg_memory_csv_header,sizeof(hg_memory_csv_header)-1);
    idle_phase=getenv("HG_MEMORY_IDLE_PHASE");
    const char *c=getenv("HG_MEMORY_CONTROL_FD");if(c)control=atoi(c);
    hg_memory_sample(output,"process_start");
}
__attribute__((destructor)) static void memory_finish(void) {
    if(output>=0){hg_memory_sample(output,"process_end");close(output);}
}
static int memory_fprintf(FILE *stream,const char *format,...) {
    va_list args, inspect;va_start(args,format);va_copy(inspect,args);
    int result=vfprintf(stream,format,args);va_end(args);
    if(output>=0&&!observing&&strstr(format,"HG_TIMING ")==format) {
        const char *phase=va_arg(inspect,const char *);
        observing=1;hg_memory_sample(output,phase);
        if(!idle_done&&control>=0&&idle_phase&&!strcmp(phase,idle_phase)) {
            idle_done=1;hg_memory_sample(output,"idle_begin");
            char reply=0;ssize_t n;
            (void)write(control,"R",1);
            for(;;) {
                fd_set ready;FD_ZERO(&ready);FD_SET(control,&ready);
                struct timeval timeout={0,250000};
                int status=select(control+1,&ready,NULL,NULL,&timeout);
                if(status==0){hg_memory_sample(output,"idle_poll");continue;}
                if(status<0&&errno==EINTR)continue;
                if(status<0)_exit(122);
                do {n=read(control,&reply,1);} while(n<0&&errno==EINTR);
                break;
            }
            if(n!=1||reply!='G')_exit(121);
            hg_memory_sample(output,"resume");
        }
        observing=0;
    }
    va_end(inspect);return result;
}
__attribute__((used,section("__DATA,__interpose")))
static const struct {const void *replacement,*original;} memory_interpose={
    (const void *)memory_fprintf,(const void *)fprintf};
