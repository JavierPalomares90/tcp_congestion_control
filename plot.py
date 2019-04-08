# Python script to plot tcp probe data generated by dumbbell_topo.py
# @author Javier Palomares

import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime as dt

SHORT_DELAY =  21
MEDIUM_DELAY = 81
LONG_DELAY =  162
DELAYS = [SHORT_DELAY, MEDIUM_DELAY, LONG_DELAY]

TCP_ALGS=['reno','cubic','bic','westwood']
TIMESTAMP_FORMAT='%Y%m%d%H%M%S'
BPS_TO_MBPS = 1024*1024

def plot_tcp_data(tcp_alg,delay):
    file_name = 'tcp_probe_{}_{}_ms_delay.txt'.format(tcp_alg,delay)
    column_names = ['Time','Sender','Receiver','Bytes','Next','Unacknowledged','Cwnd','Slow_Start_Thresh','Send_window','rtt','Receive_Window']
    # the time and cwnd for each of the 2 path
    # path one 10.0.0.3 <-> 10.0.0.1 s1<->r1
    # path two 10.0.0.4 <-> 10.0.0.2 s2<->r2
    sender1 = '10.0.0.1'
    sender2 = '10.0.0.2'
    df = pd.read_csv(file_name,names=column_names,delim_whitespace=True)
    # only look at messages from the senders (not from the receivers)
    connection1 = df[df['Sender'].str.match(sender1)]
    connection2 = df[df['Sender'].str.match(sender2)]

    ax = connection1.plot(x='Time',y='Cwnd', title='Cwnd vs time for {} at {} ms delay'.format(tcp_alg,delay),color='r')
    connection2.plot(ax=ax,x='Time',y='Cwnd', title='Cwnd vs time for {} at {} ms delay'.format(tcp_alg,delay))
    plt.xlabel('Time (seconds)')
    plt.ylabel('Send congestion window (MSS)')
    plt.legend(['Source1->Host1','Source2->Host2'],loc = 'upper right')

    save_file = 'cwnd_{}_{}_ms_delay.png'.format(tcp_alg,delay)
    plt.savefig(save_file)
    plt.show()


def plot_iperf_data(tcp_alg,delay):
    iperf_file_name1 = "iperf_{}_{}_ms_delay_1.txt".format(tcp_alg,delay)
    iperf_file_name2 = "iperf_{}_{}_ms_delay_2.txt".format(tcp_alg,delay)
    column_names = ['timestamp','source_ip','source_port','destination_ip','destination_port','group_ID','interval','transferred_bytes','bits_per_sec']
    df1 = pd.read_csv(iperf_file_name1,names=column_names)
    df2 = pd.read_csv(iperf_file_name2,names=column_names)

    # convert to a timestamp object
    df1['timestamp'] = df1['timestamp'].apply(lambda x: dt.strptime(str(x),TIMESTAMP_FORMAT) )
    df2['timestamp'] = df2['timestamp'].apply(lambda x: dt.strptime(str(x),TIMESTAMP_FORMAT) )
    
    # covert the bandwith to Mbps
    df1['bits_per_sec'] = df1['bits_per_sec'].apply(lambda x: x / BPS_TO_MBPS )
    df2['bits_per_sec'] = df2['bits_per_sec'].apply(lambda x: x / BPS_TO_MBPS )
    
    # get the start ts
    start_ts = df1.iloc[0]['timestamp']
    
    # ignore the rows with no bandwidth
    df1 = df1[df1['bits_per_sec'] != 0]
    df2 = df2[df2['bits_per_sec'] != 0]
    for index,row in df1.iterrows():
        t = row['timestamp'] - start_ts
        df1.loc[index,'timestamp'] = t.total_seconds()
    for index,row in df2.iterrows():
        t = row['timestamp'] - start_ts
        df2.loc[index,'timestamp'] = t.total_seconds()

    ax = df1.plot(x='timestamp',y='bits_per_sec',title='Bandwidth for {} at ms delay'.format(tcp_alg,delay),color='r')
    df2.plot(ax = ax, x='timestamp',y='bits_per_sec',title='Bandwidth for {} at ms delay'.format(tcp_alg,delay))
    plt.xlabel('Time (seconds)')
    plt.ylabel('Bandwidth (bps)')
    plt.legend(['Source1->Host1','Source2->Host2'],loc = 'upper right')
    save_file = "bandwidth_{}_{}_ms_delay_1.png".format(tcp_alg,delay)
    plt.savefig(save_file)
    plt.show()


def main():
    for tcp_alg in TCP_ALGS:
        for delay in DELAYS:
            plot_iperf_data(tcp_alg,delay)
            plot_tcp_data(tcp_alg,delay)



if __name__ == '__main__':
    main()