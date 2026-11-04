/* Calls the original init and instruction-elaborated original encryption. MIT */
#include <nitro.h>
#include "nitrocrypto_rc4.h"
void ProbeCrypto(void *ctx,void *key,u32 keylen,void *input,u32 size,void *output){
    CRYPTO_RC4FastInit(ctx,key,keylen);CRYPTO_RC4FastEncrypt(ctx,input,size,output);
}
