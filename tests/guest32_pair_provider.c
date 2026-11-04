/* Canonical ARM32 provider with the SOC_Poll register shape. MIT */
int PairProvider(void *pointer,unsigned count,long long timeout) {
    return pointer==0 && count==1 &&
        (timeout==0x1234567887654321LL || timeout==-1 || timeout==52365);
}
