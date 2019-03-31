#!/usr/bin/python

# Dumbell topology used for tcp assignment
# Author: Javier Palomares

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.log import lg, info
from mininet.util import irange, quietRun
from multiprocessing import Process
import os
from subprocess import Popen

# delay in ms
SHORT_DELAY =  21
MEDIUM_DELAY = 81
LONG_DELAY =  162

# how long iperf transmits in seconds
TRANSMISSION_DURATION_SECS = 10

MILLIS_TO_SEC = 1000
B_TO_MB = 1.0 / (10e6)

# packet size in bytes
PACKET_SIZE = 1500

# speed in packets per millisecond
HOST_SPEED_PACKET = 80
HOST_SPEED = HOST_SPEED_PACKET * PACKET_SIZE * MILLIS_TO_SEC * B_TO_MB

# speed in packets per millisecond
ACCESS_ROUTER_SPEED_PACKET = 21
ACCESS_ROUTER_SPEED = ACCESS_ROUTER_SPEED_PACKET * PACKET_SIZE * MILLIS_TO_SEC * B_TO_MB

# speed in packets per millisecond
BACKBONE_ROUTER_SPEED_PACKET = 82
BACKBONE_ROUTER_SPEED = BACKBONE_ROUTER_SPEED_PACKET * PACKET_SIZE * MILLIS_TO_SEC * B_TO_MB

ACCESS_ROUTER_BUFFER_PER = .20



class Dumbbell(Topo):
    def __init__(self,prop_delay):
        self.prop_delay = prop_delay
        super(Dumbbell,self).__init__()

    def build(self):

        # speed of sender/receiver to access router
        # host speed is in Mega bytes per second
        host_speed_Mbps = HOST_SPEED
        access_router_speed_Mbps = ACCESS_ROUTER_SPEED
        backbone_router_speed_Mbps = BACKBONE_ROUTER_SPEED

        # buffer size is in number of packets
        access_router_buf_packets = ACCESS_ROUTER_BUFFER_PER * ACCESS_ROUTER_SPEED_PACKET * self.prop_delay

        #left side
        # access and backbone switches
        access_router_1 = self.addSwitch('s1')
        backbone_router_1 = self.addSwitch('s2')
        # the 2 sources
        source_1 = self.addHost('h1')
        source_2 = self.addHost('h2')

        # add link from sources to access switch
        self.addLink(source_1,access_router_1, bw = host_speed_Mbps)
        self.addLink(source_2,access_router_1, bw = host_speed_Mbps)
        # add link from access to back switch
        self.addLink(access_router_1,backbone_router_1, bw = access_router_speed_Mbps, max_queue_size=access_router_buf_packets)

        # right side

        # access and backbone switches
        access_router_2 = self.addSwitch('s3')
        backbone_router_2 = self.addSwitch('s4')
        # the 2 sources
        receiver_1 = self.addHost('h3')
        receiver_2 = self.addHost('h4')
        # add link from sources to access switch
        self.addLink(receiver_1, access_router_2, bw = host_speed_Mbps)
        self.addLink(receiver_2, access_router_2, bw = host_speed_Mbps)
        # add link from access to back switch
        self.addLink(access_router_2,backbone_router_2, bw = access_router_speed_Mbps, max_queue_size=access_router_buf_packets)
        d = "{}ms".format(self.prop_delay)

        # add link between two backbone routers
        # use the propagation delay provided at construction and the hardcoded speed
        self.addLink(backbone_router_1,backbone_router_2, bw = backbone_router_speed_Mbps, delay=d)

def run_iperf(mininet, source,destination, duration_secs):
    serverbw,clientbw =  mininet.iperf([source,destination], seconds=duration_secs)
    info("server bandwith:")
    info(serverbw,'\n')
    info('\n')


def start_tcp_probe(file_name):
    os.system("rmmod tcp_probe 1> /dev/null 2>&1; "
              "modprobe tcp_probe full=1 port=5001 bufsize=10240")
    Popen("cat /proc/net/tcpprobe > ./tcp_probe_{}.txt".format(file), shell=True)

def stop_tcp_probe():
    os.system("killall -9 cat; rmmod tcp_probe")

def dumbbell_test():
    # Select TCP Reno
    info("Selecting TCP Reno\n")
    output = quietRun( 'sysctl -w net.ipv4.tcp_congestion_control=reno' )
    assert 'reno' in output
    delay = SHORT_DELAY
    info("Creating the a dumbell network with delay={}\n".format(delay))
    dumbbell = Dumbbell(delay)
    net = Mininet(dumbbell, link=TCLink)
    file_name = "reno_short_delay"
    info("starting tcp probe\n")
    start_tcp_probe(file_name)
    net.start()
    src1 = net.hosts[0]
    src2 = net.hosts[1]
    dest1 = net.hosts[2]
    dest2 = net.hosts[3]
    trans_len_sec = TRANSMISSION_DURATION_SECS
    info("transmitting for seconds {}\n".format(trans_len_sec))

    # Get a proc pool to transmit src1->dest1, src2->dest2
    p1 = Process(target=run_iperf,args=(net,src1,dest1,trans_len_sec))
    p2 = Process(target=run_iperf,args=(net,src2,dest2,trans_len_sec))


    p1.start()
    p2.start()
    # wait for the 2 threads to finish before calling .stop()
    p1.join()
    p2.join()
    info("transmission complete. shutting down\n")

    net.stop()
    stop_tcp_probe()

if __name__ =='__main__':
    setLogLevel('info')
    dumbbell_test()



