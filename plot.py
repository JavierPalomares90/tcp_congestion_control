# Python script to plot tcp probe data generated by dumbbell_topo.py
# @author Javier Palomares

import matplotlib.pyplot as plt

SHORT_DELAY =  21
MEDIUM_DELAY = 81
LONG_DELAY =  162
DELAYS = [SHORT_DELAY, MEDIUM_DELAY, LONG_DELAY]

TCP_ALGS=['reno','cubic','bic','westwood']

def plot_tcp_data(tcp_alg,delay):
    file_name = 'tcp_probe_{}_{}_ms_delay.txt'.format(tcp_alg,delay)
    # the time and cwnd for each of the 2 path
    # path one 10.0.0.3 <-> 10.0.0.1 s1<->r1
    # path two 10.0.0.4 <-> 10.0.0.2 s2<->r2
    sender1 = '10.0.0.1'
    sender2 = '10.0.0.2'
    receiver1 = '10.0.0.3'
    receiver2 = '10.0.0.4'
    times1 = []
    cwnds1 = []
    times2 = []
    cwnds2 = []
    with open(file_name,'r') as f:
        line = f.readline()
        while line:
            # read the data line by line
            tokens = line.split()
            assert len(tokens) == 11
            # Time (in seconds) since beginning of probe output
            time = float(tokens[0])
            # Source address and port of the packet, as IP:port
            sender = tokens[1]
            receiver = tokens[2]
            bytes_in_packet = int(tokens[3])
            # in hex
            next_seq_num = tokens[4]
            # Smallest sequence number of packet send but unacknowledged, in hex format
            unacked = tokens[5]
            # Size of send congestion window for this connection (in MSS)
            cwnd = int(tokens[6])
            # Size of send congestion window for this connection (in MSS)
            slow_start_thresh = int(tokens[7])
            # Send window size (in MSS). Set to the minimum of send CWND and receive window size
            send_window = int(tokens[8])
            # Smoothed estimated RTT for this connection (in ms)
            rtt = int(tokens[9])
            receiver_window = int(tokens[10])
            if sender1 in sender or sender1 in receiver:
                times1.append(time)
                cwnds1.append(cwnd)
            elif sender2 in sender or sender2 in receiver:
                times2.append(time)
                cwnds2.append(cwnd)
            else:
                raise Exception('error parsing line' + line)

            line = f.readline()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(times1,cwnds1,c='r',label='source1<->receiver1',linewidths=0.1,alpha=.5)
    ax.scatter(times2,cwnds2,c='b',label='source2<->receiver2',linewidths=0.1,alpha=.5)
    plt.title('Cwnd vs time for {} at {} ms delay'.format(tcp_alg,delay))
    plt.xlabel('Time (seconds)')
    plt.ylabel('send congestion window')
    plt.legend(loc = 'upper right')
    plt.savefig('tcp_probe_{}_{}_ms_delay.png'.format(tcp_alg,delay))
    plt.show()

def main():
    for tcp_alg in TCP_ALGS:
        for delay in DELAYS:
            plot_tcp_data(tcp_alg,delay)



if __name__ == '__main__':
    main()