/* Permission probe only: write SEB0's current bytes back unchanged.
 * No error clearing, sensor substitution, force flag, or protection override.
 */
#include <IOKit/IOKitLib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static kern_return_t call(io_connect_t c, uint8_t in[80],uint8_t out[80]) {
    size_t n=80;memset(out,0,80);
    return IOConnectCallStructMethod(c,2,in,80,out,&n);
}
int main(void) {
    io_service_t s=IOServiceGetMatchingService(kIOMainPortDefault,IOServiceMatching("AppleSMC"));
    if(!s)return 2;
    io_connect_t c=0;kern_return_t r=IOServiceOpen(s,mach_task_self(),0,&c);IOObjectRelease(s);
    if(r){printf("open kr=0x%x\n",r);return 3;}
    uint8_t in[80]={0},out[80]={0},saved[4];uint32_t key=0x53454230,n=4;
    memcpy(in,&key,4);in[42]=9;r=call(c,in,out);
    printf("SEB0 info kr=0x%x result=%u attributes=0x%x\n",r,out[40],out[36]);
    if(r||out[40]){IOServiceClose(c);return 4;}
    uint32_t actual=0;memcpy(&actual,out+28,4);
    if(actual!=4){IOServiceClose(c);return 5;}
    memcpy(in+28,&n,4);in[42]=5;r=call(c,in,out);
    if(r||out[40]){IOServiceClose(c);return 6;}
    memcpy(saved,out+48,4);
    printf("before=%02x%02x%02x%02x\n",saved[0],saved[1],saved[2],saved[3]);
    in[42]=6;memcpy(in+48,saved,4);r=call(c,in,out);
    printf("same-value write kr=0x%x result=%u status=%u\n",r,out[40],out[41]);
    in[42]=5;memset(in+48,0,4);r=call(c,in,out);
    printf("after read kr=0x%x result=%u raw=%02x%02x%02x%02x unchanged=%s\n",r,out[40],out[48],out[49],out[50],out[51],!r&&!out[40]&&!memcmp(saved,out+48,4)?"yes":"no");
    IOServiceClose(c);return 0;
}
