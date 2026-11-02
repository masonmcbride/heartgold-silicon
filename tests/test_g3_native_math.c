/* SPDX-License-Identifier: MIT */
#include <simulator/g3_native_math.h>
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
static uint32_t random_state=0x914f321;
static int32_t rnd(void) { random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;int32_t v;memcpy(&v,&random_state,4);return v; }
/* Independent wide-integer oracle, including values that overflow signed 64.
 * Taking low 32 bits AFTER the sum/shift differs from FX_Mul rounding. */
static int32_t oracle(__int128 n) { uint32_t u=(uint32_t)(n>>12);int32_t v;memcpy(&v,&u,4);return v; }
int main(void)
{
    G3NativeMatrix a[16],b[16],out[16];
    for(unsigned n=0;n<16;++n)for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j){a[n].m[i][j]=rnd();b[n].m[i][j]=rnd();}
    G3Native_MultiplyScalar(out,a,b,16);
    for(unsigned n=0;n<16;++n)for(unsigned r=0;r<4;++r)for(unsigned c=0;c<4;++c){
        __int128 sum=0;for(unsigned k=0;k<4;++k)sum+=(__int128)a[n].m[r][k]*b[n].m[k][c];
        assert(out[n].m[r][c]==oracle(sum));
    }
    G3Native_MultiplyScalar(a,a,b,16);assert(!memcmp(a,out,sizeof(a)));
    G3NativeMatrix identity;G3Native_Identity(&identity);
    G3NativeVector vertices[128],expected[128];
    for(unsigned n=0;n<128;++n)for(unsigned i=0;i<4;++i)vertices[n].v[i]=rnd();
    G3Native_TransformScalar(expected,vertices,128,&identity);assert(!memcmp(vertices,expected,sizeof(vertices)));
    identity.m[3][0]=4096;identity.m[0][1]=8192;
    G3NativeVector v={{4096,8192,12288,4096}};
    G3Native_TransformScalar(&v,&v,1,&identity);
    assert(v.v[0]==8192&&v.v[1]==16384&&v.v[2]==12288&&v.v[3]==4096);
    G3NativeVertex triangle[3]={0},clipped[12];
    for(unsigned i=0;i<3;++i){triangle[i].position[3]=4096;triangle[i].color[0]=31;}
    triangle[0].position[0]=-8192;triangle[1].position[0]=2048;triangle[2].position[1]=2048;
    int n=G3Native_ClipScalar(clipped,12,triangle,3,1);assert(n==4);
    for(int i=0;i<n;++i){for(unsigned c=0;c<3;++c)assert(clipped[i].position[c]>=-clipped[i].position[3]&&clipped[i].position[c]<=clipped[i].position[3]);assert(clipped[i].color[0]==31);}
    triangle[0].position[2]=8192;assert(G3Native_ClipScalar(clipped,12,triangle,3,0)==0);
    assert(G3Native_ClipScalar(clipped,2,triangle,3,1)==-1);
    G3NativeLighting lights={0};lights.enabled=1;lights.diffuse[0]=31;lights.color[0][0]=31;lights.direction[0][2]=-512;
    G3NativeVector normal={{0,0,511,0}};uint8_t rgb[1][3];
    G3Native_LightScalar(rgb,&normal,1,&lights);assert(rgb[0][0]==29&&rgb[0][1]==0&&rgb[0][2]==0);
    normal.v[2]=-511;G3Native_LightScalar(rgb,&normal,1,&lights);assert(rgb[0][0]==0);
    puts("native G3 matrix/transform batch, overflow, clipping and lighting passed");
}
