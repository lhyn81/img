import usb.core
import usb.util
import sys
import time
import csv
import binascii
from struct import *
from ctypes import *

################# Class MicroNIR ##################
class nir:
    def __init__(self,vid,pid):
        self.VID=vid
        self.PID=pid
        self.dev =  usb.core.find(idVendor= vid, idProduct= pid)
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]
        self.epw = usb.util.find_descriptor(intf,custom_match = lambda e:usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_OUT)
        self.epr = usb.util.find_descriptor(intf,custom_match = lambda e:usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_IN)
        self.wvl=[0]*128
        self.full=[0]*128
        self.dark=[0]*128
        self.sample=[0]*128

    def gen_wvl(self):
        self.wvl[0]=908.0
        for i in range(1,127):
            self.wvl[i]=self.wvl[i-1]+6.19

    def sendcmd(self,cmd):
        cmd= cmd + "\r"
        #print('>>>Command:',cmd)
        ret=self.epw.write(cmd)

    def recvdata(self):
        idx=[]
        ret=[]
        for i in range(1,128):
            idx.append(4*i)
            idx.append(4*i+1)
        #print(idx)

        for i in range(1,10):
            data = self.epr.read(700)
            if len(data)>500:
                final_data=[data[x] for x in idx]
                for j in range(0,127):
                    bl=final_data[j*2]
                    bh=final_data[j*2+1]
                    s=unpack("!H",bytearray([bl,bh]))
                    ret.append(s[0])
        return ret

    def dump_BaseData(self):
        base=[]
        for i in range(0,127):
            base.append([self.wvl[i],self.full[i],self.dark[i]])
        with open("./base.csv","wb") as output:
            wr=csv.writer(output,lineterminator='\n')
            wr.writerows(base)

    def read_list(self):
        with open('./base.csv','rb') as f:
            reader =  csv.reader(f)
            full_list = map(tuple,reader)
            print(full_list[79][1])
            print(full_list[80][1])

    def dump_SampleData(self):
        with open('./base.csv','rb') as f:
            reader =  csv.reader(f)
            full_list = map(tuple,reader)
            wvl100_a=int(full_list[79][1])
            wvl100_b=int(full_list[80][1])
            wvl100=(wvl100_a+wvl100_b)/2.0

        with open("./sample.csv","w") as output:
            wr=csv.writer(output,lineterminator='\n')
            wr.writerow(self.sample)

        wvl1400=(self.sample[80]+self.sample[81])/2
        print(wvl1400)
        x=(wvl100-wvl1400)/wvl100
        absorption=1.759*x**3-0.9846*x**2+0.6872*x-0.002124

        return absorption

    def release(self):
        usb.util.dispose_resources(self.dev)

