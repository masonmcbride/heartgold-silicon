#include <nitro.h>
#include <simulator/sim.h>
#include <simulator/sim_audio.h>

#include <nitro/wm/ARM7/wm_sp.h>

#include "wmsp_private.h"

#include <ntr_host.h>
#include "../audio/native_audio.h"

#ifdef SDK_TRACY_ENABLE
#include "tracy/TracyC.h"
#endif

SIM_queue_t * drawQueuePtr;
SIM_queue_t * pxiQueuePtr;
SIM_queue_t * pxi7to9QueuePtr;

static SIM_queue_t SIM_drawQueue;
static SIM_queue_t SIM_pxiQueue;
static SIM_queue_t SIM_pxi7to9Queue;

extern PXIFifoCallback FifoRecvCallbackTable7[PXI_MAX_FIFO_TAG];

static HG_Semaphore * pxiSemaphore;
static HG_Semaphore * pxi7to9Semaphore;
static HG_Semaphore * osThreadSemaphore;

void SIM_pxiInit(void)
{
    SIM_drawQueue.head = 0;
    SIM_drawQueue.tail = 0;
    SIM_drawQueue.size = 2048;
    SIM_drawQueue.data = malloc( sizeof(void*) * 4096 );

	drawQueuePtr = &SIM_drawQueue;

    SIM_pxiQueue.head = 0;
    SIM_pxiQueue.tail = 0;
    SIM_pxiQueue.size = 2048;
    SIM_pxiQueue.data = malloc( sizeof(void*) * 4096 );

	pxiQueuePtr = &SIM_pxiQueue;

    SIM_pxi7to9Queue.head = 0;
    SIM_pxi7to9Queue.tail = 0;
    SIM_pxi7to9Queue.size = 2048;
    SIM_pxi7to9Queue.data = malloc( sizeof(void*) * 4096 );

	pxi7to9QueuePtr = &SIM_pxi7to9Queue;

	pxiSemaphore = HG_CreateSemaphore(0);
	pxi7to9Semaphore = HG_CreateSemaphore(0);
}

void SIM_procPXI(void)
{

	void * data;
	data = SIM_queue_read( pxiQueuePtr );
	while( data != NULL )
	{
		WIN_PXIFifoMessage * msg;
		msg = (WIN_PXIFifoMessage *)data;

		switch( msg->e.tag )
		{
			case PXI_FIFO_TAG_TOUCHPANEL:

				break;
			case PXI_FIFO_TAG_SOUND:
				{
					SNDCommand * sndCommandList;
					sndCommandList = (SNDCommand * )msg->e.data;

					if( sndCommandList == NULL )
					{
						break;
					}
					HG_SoundLock();
					while( sndCommandList != NULL ){
						switch( sndCommandList->id )
						{
                        case SND_COMMAND_START_TIMER:
                            if (sndCommandList->arg[1]) { fputs("Native sound capture is not implemented\n", stderr); abort(); }
                            for (int i=0; i<16; ++i)
                                if (sndCommandList->arg[0] & (1u<<i)) SND_StartChannel7(i);
                            for (int i=0; i<32; ++i) {
                                if (!(sndCommandList->arg[2] & (1u<<i))) continue;
                                if (win_snd_alarms[i].isRunning) {
                                    win_snd_alarms[i].isRunning=0;
                                    pthread_join(win_snd_alarms[i].thread,NULL);
                                }
                                win_snd_alarms[i].isRunning=1;
                                if (pthread_create(&win_snd_alarms[i].thread,NULL,SIM_sndAlarm,&win_snd_alarms[i])) abort();
                            }
                            break;
                        case SND_COMMAND_STOP_TIMER:
                            if (sndCommandList->arg[1]) { fputs("Native sound capture is not implemented\n", stderr); abort(); }
                            for (int i=0; i<16; ++i)
                                if (sndCommandList->arg[0] & (1u<<i)) SND_StopChannel7(i,sndCommandList->arg[3]);
                            for (int i=0; i<32; ++i) {
                                if (!(sndCommandList->arg[2] & (1u<<i))) continue;
                                if (win_snd_alarms[i].isRunning) {
                                    win_snd_alarms[i].isRunning=0;
                                    pthread_join(win_snd_alarms[i].thread,NULL);
                                }
                            }
                            break;
                        case SND_COMMAND_SETUP_CAPTURE:
                            fputs("Native sound capture is not implemented\n",stderr); abort();
            				case SND_COMMAND_SETUP_ALARM:

								win_snd_alarms[sndCommandList->arg[0]].alarmNo = sndCommandList->arg[0];
								win_snd_alarms[sndCommandList->arg[0]].time = sndCommandList->arg[1];
								win_snd_alarms[sndCommandList->arg[0]].period = sndCommandList->arg[2];
								win_snd_alarms[sndCommandList->arg[0]].id = sndCommandList->arg[3];
            				    break;

                        default:
                            HG_SoundCommand(sndCommandList);
                            break;
                        }
						sndCommandList = sndCommandList->next;
					} 
						if( win_SNDi_SharedWork )
						{
							win_SNDi_SharedWork->finishCommandTag++;
						}
                        HG_SoundUnlock();
					
				}
				break;
            case PXI_FIFO_TAG_WM:

                {

					if(FifoRecvCallbackTable7[PXI_FIFO_TAG_WM]) {
						FifoRecvCallbackTable7[PXI_FIFO_TAG_WM](PXI_FIFO_TAG_WM, msg->e.data, (BOOL)msg->e.err);
					}
                }
                break;
			case PXI_FIFO_TAG_OS: {

				u32 pxiData = msg->e.data;
				u32 osCommand = pxiData >> 8 ;
				switch(osCommand) {
					case 0x10 :
						OS_Printf("Reset command received.\n");
						break;
					default:
						break;
				}
			} break;
            case PXI_FIFO_TAG_NVRAM: {
                if (FifoRecvCallbackTable7[PXI_FIFO_TAG_NVRAM])
                    FifoRecvCallbackTable7[PXI_FIFO_TAG_NVRAM](
                        PXI_FIFO_TAG_NVRAM, msg->e.data, (BOOL)msg->e.err);
            } break;
			case PXI_FIFO_TAG_WVR: {
				if(FifoRecvCallbackTable7[PXI_FIFO_TAG_WVR]) {
					FifoRecvCallbackTable7[PXI_FIFO_TAG_WVR](PXI_FIFO_TAG_WVR, msg->e.data, (BOOL)msg->e.err);
				}
			} break;
			default:
				break;
		}

		free( data );

		data = SIM_queue_read( pxiQueuePtr );

	}
}

void SIM_procPXI7to9(void)
{

	void * data;
	data = SIM_queue_read( pxi7to9QueuePtr );
	while( data != NULL)
	{
		WIN_PXIFifoMessage * msg;
		msg = (WIN_PXIFifoMessage *)data;

		PXIFifoCallback myCallback = NULL;

		myCallback = PXI_WIN_GetCallback(msg->e.tag);

		if( myCallback != NULL )
		{
			myCallback(msg->e.tag, msg->e.data, msg->e.err);
		}

		free( data );
		
		data = SIM_queue_read( pxi7to9QueuePtr );
	}
}

int SIM_procPxiThread( void * arg )
{
	while(1)
	{
		HG_SemWait(pxiSemaphore);
		#ifdef SDK_TRACY_ENABLE
		TracyCZone(ctx, 1);
		#endif
		SIM_procPXI();
		#ifdef SDK_TRACY_ENABLE
		TracyCZoneEnd(ctx);
		#endif
	}
	return 0;
}

void SIM_PostPxiThread()
{
	HG_SemPost(pxiSemaphore);
}

int SIM_procPxi7to9Thread( void * arg )
{
	while(1)
	{
		HG_SemWait(pxi7to9Semaphore);
		#ifdef SDK_TRACY_ENABLE
		TracyCZone(ctx, 1);
		#endif
		SIM_procPXI7to9();
		#ifdef SDK_TRACY_ENABLE
		TracyCZoneEnd(ctx);
		#endif
	}
	return 0;
}

void SIM_PostPxi7to9Thread()
{
	HG_SemPost(pxi7to9Semaphore);
}

void * SIM_sndAlarm(void * arg)
{
	WIN_snd_alarm_info * sndAlarmInfo;
	sndAlarmInfo = (WIN_snd_alarm_info *)arg;
	u32 timeMs;
	u32 periodMs;

	double timeSec = (double)(sndAlarmInfo->time * 32.0f) / (double)SND_TIMER_CLOCK;
	timeMs = (u32)(timeSec * 1000.0f);
	double periodSec = (double)(sndAlarmInfo->period * 32.0f) / (double)SND_TIMER_CLOCK;
	periodMs = (u32)(periodSec * 1000.0f);
	HG_Delay( timeMs );
	SNDi_CallAlarmHandler( sndAlarmInfo->alarmNo | (sndAlarmInfo->id) <<8 );

	if( sndAlarmInfo->period != 0 )
	{
		while( 1 )
		{
			if( !sndAlarmInfo->isRunning )
			{
				return NULL;
			}
			HG_Delay( periodMs );
			SNDi_CallAlarmHandler( sndAlarmInfo->alarmNo | (sndAlarmInfo->id) <<8 );
		}
	}

}