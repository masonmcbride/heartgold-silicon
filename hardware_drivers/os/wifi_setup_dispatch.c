/*
 * Native executable ABI boundary for the original OVY_13 WFC entry.
 * The real implementation remains owned by OVY_13.
 */
#include <dlfcn.h>
#include <stdlib.h>

void HG_DispatchWifiSetupApp(int heap_id)
{
    typedef void (*Entry)(int);
    Entry entry = (Entry)dlsym(RTLD_NEXT, "RunWifiSetupApp");

    /* An unavailable original overlay is an error, not a successful
       emulation of the Nintendo WFC setup application. */
    if (entry == NULL)
        abort();

    entry(heap_id);
}

/* Native ABI for the original MSL_C atod(const char *) entry.
 * The host double parser preserves the binary64 return ABI.
 */
double atod(const char *text)
{
    return strtod(text, NULL);
}


/*
 * Main-image entry point for callers compiled without the
 * native source-name adaptation.
 *
 * Forward to the original overlay implementation.
 */
void RunWifiSetupApp(int heap_id)
{
    HG_DispatchWifiSetupApp(heap_id);
}
