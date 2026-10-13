/* Probe ordinary access to diagnostic selectors without issuing a reset.
 * Only all-zero, already-zero MSFL and MSFN values may be written.
 */
#include <IOKit/IOKitLib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uint32_t keycode(const char *s){return (uint32_t)s[0]<<24|(uint32_t)s[1]<<16|(uint32_t)s[2]<<8|(uint8_t)s[3];}
static kern_return_t call(io_connect_t c,uint8_t in[80],uint8_t out[80]){size_t n=80;memset(out,0,80);return IOConnectCallStructMethod(c,2,in,80,out,&n);}
int main(void){
 io_service_t s=IOServiceGetMatchingService(kIOMainPortDefault,IOServiceMatching("AppleSMC"));if(!s)return 2;
 io_connect_t c=0;kern_return_t r=IOServiceOpen(s,mach_task_self(),0,&c);IOObjectRelease(s);if(r)return 3;
 const char *keys[]={"MSFL","MSFN"};uint32_t expected[]={4,1};
 for(int k=0;k<2;k++){
  uint8_t in[80]={0},out[80]={0};uint32_t key=keycode(keys[k]),n=0;memcpy(in,&key,4);in[42]=9;
  r=call(c,in,out);memcpy(&n,out+28,4);printf("%s info kr=0x%x result=%u attributes=0x%x size=%u\n",keys[k],r,out[40],out[36],n);
  if(r||out[40]||n!=expected[k])break;
  memcpy(in+28,&n,4);in[42]=5;r=call(c,in,out);if(r||out[40])break;
  int nonzero=0;for(unsigned j=0;j<n;j++)nonzero|=out[48+j];
  if(nonzero){printf("%s nonzero diagnostic state, probe aborted\n",keys[k]);break;}
  printf("%s before zero\n",keys[k]);in[42]=6;r=call(c,in,out);
  printf("%s zero/no-op write kr=0x%x result=%u status=%u\n",keys[k],r,out[40],out[41]);
  in[42]=5;r=call(c,in,out);nonzero=0;for(unsigned j=0;j<n;j++)nonzero|=out[48+j];
  printf("%s after kr=0x%x result=%u zero=%s\n",keys[k],r,out[40],nonzero?"no":"yes");
 }
 IOServiceClose(c);return 0;
}
