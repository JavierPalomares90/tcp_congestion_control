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
from multiprocessing import Process,Queue
import os
import time
from subprocess import Popen

# delay in ms
SHORT_DELAY =  21
MEDIUM_DELAY = 81
LONG_DELAY =  162
DELAYS = [SHORT_DELAY, MEDIUM_DELAY, LONG_DELAY]
PORT = 5001

SECOND_TRANSMISSION_DELAY_SECS = 25

TCP_ALGS=['reno','cubic','bic','westwood']

# how long iperf transmits in seconds
TRANSMISSION_DURATION_SECS = 100

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

def run_iperf(q, source, destination, duration_secs,portNum,tcp_alg,file_name):
    info('Starting iperf from source {} to destination {}\n'.format(source,destination))
    info('Starting the destination on port {}\n'.format(portNum))
    p2 = destination.popen('iperf -s -p {}&'.format(portNum),shell=True)

    info('Starting the source\n')
    # may have to use popen instead
    destinationIP = destination.IP()
    cmd = 'iperf -c {} -p {} -i 1 -w 16m -Z {} -t {} -y c > {}'.format(destinationIP,portNum,tcp_alg,duration_secs,file_name)
    info('Source executing:{}\n'.format(cmd))
    p1 = source.popen(cmd, shell=True)
    # return the p objects in the queue
    q.put([p1,p2])
    # wait until command is done
    (output, err) = p1.communicate()
    p_status = p1.wait()
    info('output:{}, err={},status={}'.format(output,err,p_status))
    p2.kill()


def start_tcp_probe(file_name):
    os.system("rmmod tcp_probe 1> /dev/null 2>&1; "
              "modprobe tcp_probe full=1")
    Popen("cat /proc/net/tcpprobe > ./tcp_probe_{}.txt".format(file_name), shell=True)

def stop_tcp_probe():
    os.system("killall -9 cat; rmmod tcp_probe")

def dumbbell_test(tcp_alg,delay):
    info("Setting tcp alg to {}\n".format(tcp_alg))
    out = quietRun('mn -c')
    info('mn -c: {}\n'.format(out))
    output = quietRun( 'sysctl -w net.ipv4.tcp_congestion_control={}'.format(tcp_alg))
    assert tcp_alg in output
    info("Creating the a dumbell network with delay={}\n".format(delay))
    dumbbell = Dumbbell(delay)
    net = Mininet(dumbbell, link=TCLink)

    file_name = "{}_{}_ms_delay".format(tcp_alg,delay)
    iperf_file_name1 = "iperf_{}_{}_ms_delay_1.txt".format(tcp_alg,delay)
    iperf_file_name2 = "iperf_{}_{}_ms_delay_2.txt".format(tcp_alg,delay)
    info("Starting the topology\n")
    net.start()
    info("Dumping node connections\n")
    dumpNodeConnections(net.hosts)
    info("Starting tcp probe\n")
    start_tcp_probe(file_name)
    src1 = net.hosts[0]
    src2 = net.hosts[1]
    dest1 = net.hosts[2]
    dest2 = net.hosts[3]
    trans_len_sec = TRANSMISSION_DURATION_SECS
    info("Transmitting for {} seconds.\n".format(trans_len_sec))
    q1 = Queue()
    q2 = Queue()

    # Get a proc pool to transmit src1->dest1, src2->dest2
    p1 = Process(target=run_iperf,args=(q1,src1,dest1,trans_len_sec,5001,tcp_alg,iperf_file_name1))
    p2 = Process(target=run_iperf,args=(q2,src2,dest2,trans_len_sec,5002,tcp_alg,iperf_file_name2))


    p1.start()
    info("Waiting for {} secs before starting second connection\n".format(SECOND_TRANSMISSION_DELAY_SECS))
    # wait for SECOND_TRANSMISSION_DELAY_SECS before starting the second transmission
    time.sleep(SECOND_TRANSMISSION_DELAY_SECS)
    p2.start()

    # get the popens from each of the 2 iperf runs
    popen1 = q1.get()[0]
    popen2 = q1.get()[1]
    # wait until connection 1 is done
    (output, err) = popen1.communicate()
    p_status = popen1.wait()
    info('output:{}, err={},status={}'.format(output,err,p_status))
    popen2.kill()

    popen3 = q2.get()[0]
    popen4 = q2.get()[1]

    # wait until connection 2 is done
    (output, err) = popen3.communicate()
    p_status = popen3.wait()
    info('output:{}, err={},status={}'.format(output,err,p_status))
    popen4.kill()
    info("Transmission complete. Shutting down\n")

    net.stop()
    stop_tcp_probe()

def main():
    setLogLevel('info')
    # run reno over each of the 3 delays
    for tcp_alg in TCP_ALGS:
        for delay in DELAYS:
            info("Testing TCP {} with delay to {} ms\n".format(tcp_alg,delay))
            dumbbell_test(tcp_alg,delay)

if __name__ =='__main__':
    main()



