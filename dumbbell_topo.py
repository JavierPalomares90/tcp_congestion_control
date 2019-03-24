#!/usr/bin/python

# Dumbell topology used for tcp assignment
# Author: Javier Palomares

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

SHORT = "21ms"
MEDIUM = "81ms"
LONG = "162ms"

class Dumbbell(Topo):
    def __init__(self,prop_delay):
        super(Dumbbell,self).__init__()
        self.prop_delay = prop_delay

    def build(self):
        #left side
        # access and backbone switches
        access_router_1 = self.addSwitch('s1')
        backbone_router_1 = self.addSwitch('s2')
        # the 2 sources
        source_1 = self.addHost('h1')
        source_2 = self.addHost('h2')
        # add link from sources to access switch
        self.addLink(source_1,access_router_1)
        self.addLink(source_2,access_router_1)
        # add link from access to back switch
        self.addLink(access_router_1,backbone_router_1)

        # right side

        # access and backbone switches
        access_router_2 = self.addSwitch('s3')
        backbone_router_2 = self.addSwitch('s4')
        # the 2 sources
        receiver_1 = self.addHost('h3')
        receiver_2 = self.addHost('h4')
        # add link from sources to access switch
        self.addLink(receiver_1, access_router_2)
        self.addLink(receiver_2, access_router_2)
        # add link from access to back switch
        self.addLink(access_router_2,backbone_router_2)

        # add link between two backbone routers
        # use the propagation delay provided at construction
        self.addLink(backbone_router_1,backbone_router_2,delay=self.prop_delay)


def simple_test():
    "Create and test a dumbell network"
    dumbbell = Dumbbell(SHORT)
    net = Mininet(dumbbell)
    net.start()
    print("Dumping host connections")
    dumpNodeConnections(net.hosts)
    print("Testing network connectivity")
    net.pingAll()
    net.stop()

if __name__ =='__main__':
    setLogLevel('info')
    simple_test()



