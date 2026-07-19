#include "sha256.h"
#include <string.h>

static const uint32_t k[64] = {
0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u};
static uint32_t rr(uint32_t x,unsigned n){return(x>>n)|(x<<(32u-n));}
static void transform(PSXSha256*c,const uint8_t*b){uint32_t w[64];for(int i=0;i<16;i++)w[i]=((uint32_t)b[i*4]<<24)|((uint32_t)b[i*4+1]<<16)|((uint32_t)b[i*4+2]<<8)|b[i*4+3];for(int i=16;i<64;i++){uint32_t a=rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>3),z=rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>10);w[i]=w[i-16]+a+w[i-7]+z;}uint32_t a=c->state[0],b0=c->state[1],d0=c->state[2],d=c->state[3],e=c->state[4],f=c->state[5],g=c->state[6],h=c->state[7];for(int i=0;i<64;i++){uint32_t s1=rr(e,6)^rr(e,11)^rr(e,25),ch=(e&f)^((~e)&g),t1=h+s1+ch+k[i]+w[i],s0=rr(a,2)^rr(a,13)^rr(a,22),maj=(a&b0)^(a&d0)^(b0&d0),t2=s0+maj;h=g;g=f;f=e;e=d+t1;d=d0;d0=b0;b0=a;a=t1+t2;}c->state[0]+=a;c->state[1]+=b0;c->state[2]+=d0;c->state[3]+=d;c->state[4]+=e;c->state[5]+=f;c->state[6]+=g;c->state[7]+=h;}
void psx_sha256_init(PSXSha256*c){static const uint32_t s[8]={0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u};memcpy(c->state,s,sizeof(s));c->bit_count=0;c->block_len=0;}
void psx_sha256_update(PSXSha256*c,const void*data_,size_t len){const uint8_t*data=(const uint8_t*)data_;c->bit_count+=(uint64_t)len*8u;while(len){size_t n=64u-c->block_len;if(n>len)n=len;memcpy(c->block+c->block_len,data,n);c->block_len+=n;data+=n;len-=n;if(c->block_len==64u){transform(c,c->block);c->block_len=0;}}}
void psx_sha256_final(PSXSha256*c,uint8_t out[32]){c->block[c->block_len++]=0x80;if(c->block_len>56u){memset(c->block+c->block_len,0,64u-c->block_len);transform(c,c->block);c->block_len=0;}memset(c->block+c->block_len,0,56u-c->block_len);for(int i=0;i<8;i++)c->block[63-i]=(uint8_t)(c->bit_count>>(i*8));transform(c,c->block);for(int i=0;i<8;i++){out[i*4]=(uint8_t)(c->state[i]>>24);out[i*4+1]=(uint8_t)(c->state[i]>>16);out[i*4+2]=(uint8_t)(c->state[i]>>8);out[i*4+3]=(uint8_t)c->state[i];}memset(c,0,sizeof(*c));}
void psx_sha256(const void*d,size_t n,uint8_t out[32]){PSXSha256 c;psx_sha256_init(&c);psx_sha256_update(&c,d,n);psx_sha256_final(&c,out);}
void psx_sha256_hex(const uint8_t d[32],char out[65]){static const char h[]="0123456789abcdef";for(int i=0;i<32;i++){out[i*2]=h[d[i]>>4];out[i*2+1]=h[d[i]&15];}out[64]='\0';}
