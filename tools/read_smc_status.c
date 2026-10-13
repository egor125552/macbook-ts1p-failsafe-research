#include <IOKit/IOKitLib.h>
#include <CoreFoundation/CoreFoundation.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t keycode(const char *s) {
    return ((uint32_t)(uint8_t)s[0]<<24)|((uint32_t)(uint8_t)s[1]<<16)|
           ((uint32_t)(uint8_t)s[2]<<8)|(uint8_t)s[3];
}
int main(int argc, char **argv) {
    io_service_t service=IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("AppleSMC"));
    io_name_t name={0}; IORegistryEntryGetName(service,name);
    printf("service=%u name=%s\n",service,name);
    if (!service) return 2;
    if(argc==2 && strcmp(argv[1],"--parents")==0) {
        io_registry_entry_t e=service;
        for(int i=0;i<18;i++) {
            io_name_t nm={0},cls={0};IORegistryEntryGetName(e,nm);IOObjectGetClass(e,cls);
            printf("parent[%d] name=%s class=%s\n",i,nm,cls);
            const char *keys[]={"role","FirmwareVersion","FirmwareUUID","RTKitVersion"};
            for(int k=0;k<4;k++){
                CFStringRef key=CFStringCreateWithCString(NULL,keys[k],kCFStringEncodingUTF8);
                CFTypeRef val=IORegistryEntryCreateCFProperty(e,key,NULL,0);
                if(val){printf("%s=",keys[k]);CFShow(val);CFRelease(val);}CFRelease(key);
            }
            io_registry_entry_t next=0;
            kern_return_t r=IORegistryEntryGetParentEntry(e,kIOServicePlane,&next);
            IOObjectRelease(e);if(r)break;e=next;
        }
        return 0;
    }
    io_connect_t conn=0;
    kern_return_t kr=IOServiceOpen(service,mach_task_self(),0,&conn);
    IOObjectRelease(service);
    printf("open=0x%x conn=%u\n",kr,conn);
    if (kr) return 3;
    if(argc==2 && (strcmp(argv[1],"--enumerate")==0 || strcmp(argv[1],"--writable")==0)) {
        int permissions=strcmp(argv[1],"--writable")==0;
        for(uint32_t index=0;index<4096;index++) {
            uint8_t in[80]={0},out[80]={0};size_t size=sizeof(out);
            memcpy(in+44,&index,4);in[42]=8;
            kr=IOConnectCallStructMethod(conn,2,in,sizeof(in),out,&size);
            if(kr || out[40]) break;
            uint32_t k=0;memcpy(&k,out,4);
            if(!k)break;
            if(permissions) {
                memset(in,0,sizeof(in));memcpy(in,&k,4);in[42]=9;size=sizeof(out);
                kr=IOConnectCallStructMethod(conn,2,in,sizeof(in),out,&size);
                uint32_t n=0;memcpy(&n,out+28,4);
                if(!kr && !out[40] && (out[36]&0x40))
                    printf("%u %c%c%c%c attributes=%02x size=%u\n",index,(k>>24)&255,(k>>16)&255,(k>>8)&255,k&255,out[36],n);
            } else printf("%u %c%c%c%c\n",index,(k>>24)&255,(k>>16)&255,(k>>8)&255,k&255);
        }
        IOServiceClose(conn);return 0;
    }
    for(int i=1;i<argc;i++) {
        if(strlen(argv[i])!=4) continue;
        uint8_t in[168]={0},out[168]={0};size_t size=80;
        uint32_t key=keycode(argv[i]); memcpy(in,&key,4);in[42]=9;
        kr=IOConnectCallStructMethod(conn,2,in,80,out,&size);
        uint32_t n=0,type=0;memcpy(&n,out+28,4);memcpy(&type,out+32,4);
        printf("%s info kr=0x%x result=%u status=%u len=%zu size=%u type=0x%x attributes=0x%x\n",argv[i],kr,out[40],out[41],size,n,type,out[36]);
        if(kr || out[40] || n==0 || n>120) continue;
        size_t request_size=n>32 ? 168 : 80;
        memset(out,0,sizeof(out));memcpy(in+28,&n,4);in[42]=5;size=request_size;
        kr=IOConnectCallStructMethod(conn,2,in,request_size,out,&size);
        printf("%s read kr=0x%x result=%u status=%u raw=",argv[i],kr,out[40],out[41]);
        for(uint32_t j=0;j<n;j++)printf("%02x",out[48+j]);
        if(n==4){float f;memcpy(&f,out+48,4);printf(" float=%g",f);} puts("");
    }
    IOServiceClose(conn);
    return 0;
}
