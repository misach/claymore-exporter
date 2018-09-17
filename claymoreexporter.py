#!/usr/bin/env python

from prometheus_client import start_http_server, Gauge, Counter
import argparse
import time
from claymoreexporter_lib import netcat, validIP

version = 0.50

# Parse commandline arguments
parser = argparse.ArgumentParser(description="Claymore Prometheus exporter v" + str(version))
parser.add_argument("-t", "--target", metavar="<ip>", required=True, help="Target IP Address", type=validIP)
parser.add_argument("-f", "--frequency", metavar="<seconds>", required=False, help="Interval in seconds between checking measures", default=1, type=int)
parser.add_argument("-p", "--port", metavar="<port>", required=False, help="Port for listenin", default=8601, type=int)
parser.add_argument("-c", "--claymoreport", metavar="<claymoreport>", required=False, help="Port where claymore will be watching", default=3333, type=int)
args = parser.parse_args()

# Set target IP, port and command to send
ip = args.target
listen_port = args.port
sleep_time = args.frequency
port = args.claymoreport

received_data = {'claymore_version': '', 'running_time': '', 'gpu': {} , 'coin1': {}, 'coin2': {}}

REQUEST_GPU_TEMP  = Gauge('claymore_gpu_temp','Claymore GPU temp', ['gpu_id'])
REQUEST_GPU_FAN  = Gauge('claymore_gpu_fan','Claymore GPU fan', ['gpu_id'])
REQUEST_GPU_HR1  = Gauge('claymore_gpu_hashrate_1','Claymore GPU hashrate1', ['gpu_id'])
REQUEST_GPU_HR2  = Gauge('claymore_gpu_hashrate_2','Claymore GPU hashrate2', ['gpu_id'])
REQUEST_GPU_PCI = Gauge('claymore_gpu_pci','Claymore GPU pci slot', ['gpu_id'])
REQUEST_GPU_ETH_SHARES_ACCEPTED = Gauge('claymore_gpu_eth_shares_accepted','Claymore GPU ETH accepted shares', ['gpu_id'])
REQUEST_GPU_ETH_SHARES_REJECTED = Gauge('claymore_gpu_eth_shares_rejected','Claymore GPU ETH rejected shares', ['gpu_id'])
REQUEST_GPU_ETH_SHARES_INVALIDE = Gauge('claymore_gpu_eth_shares_invalide','Claymore GPU ETH invalide shares', ['gpu_id'])

REQUEST_INFO        =  Gauge('claymore_info', 'Claymore informations',['version','dcr_mining_pool','eth_mining_pool'])
REQUEST_RUNNING_TIME =  Gauge('claymore_running_time','Claymore Miner Running Time')

REQUEST_COIN1_SHARES = Counter('claymore_coin1_shares','Claymore coin1 share')
REQUEST_COIN1_REJECT = Counter('claymore_coin1_shares_reject','Claymore coin1 share reject')
REQUEST_COIN2_SHARES = Counter('claymore_coin2_shares','Claymore coin2 share')
REQUEST_COIN2_REJECT = Counter('claymore_coin2_shares_reject','Claymore coin2 share reject')

if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(listen_port)

    # Main loop
    while True:

        # Getting Miner Data with json rpc minder_getstat2 API0
        data = netcat(ip, port, '{"id":0,"jsonrpc":"2.0","method":"miner_getstat2"}' )

        # print data
        # Get Claymore version and running time from raw data
        received_data['claymore_version'] = data['result'][0]
        received_data['running_time'] = data['result'][1]

        # sample received_data received_data:
        #
        # {'claymore_version': u'11.3 - ETH',
        #    'coin2': {'total_hashrate': u'0', 'shares': u'0', 'reject': u'0'},
        #    'coin1': {'total_hashrate': u'116245', 'shares': u'462', 'reject': u'0'},
        #      'gpu': {0: {'hashrate2': 0, 'hashrate1': u'29161', 'fan': u'40', 'temp': u'64'},
        #              1: {'hashrate2': 0, 'hashrate1': u'29171', 'fan': u'40', 'temp': u'67'},
        #              2: {'hashrate2': 0, 'hashrate1': u'27806', 'fan': u'43', 'temp': u'65'},
        #              3: {'hashrate2': 0, 'hashrate1': u'30105', 'fan': u'37', 'temp': u'73'}},
        # 'running_time': u'679'}

        if (received_data['claymore_version'] == "No client"):

            # No data array:
            # received_data {'claymore_version': u'No client', 'coin2': {}, 'coin1': {}, 'gpu': {}, 'running_time': u'6'}

            for i in range (0,len(received_data['gpu'])):
                received_data['gpu'][i]['hashrate1'] = 0
                received_data['gpu'][i]['hashrate2'] = 0
                received_data['gpu'][i]['temp'] = 0
                received_data['gpu'][i]['fan']  = 0

        REQUEST_RUNNING_TIME.set(received_data['running_time'])

        # Get total hash rate from Claymore raw data
        total_coin_array = data['result'][2].split(';')
        received_data['coin1']['total_hashrate'] = total_coin_array[0]

        # Get Shares accepted/rejeted from raw data, and update last share/reject info
        if 'shares' in received_data['coin1']:
            last_share1  = int(received_data['coin1']['shares'])
        else:
            last_share1  = int(total_coin_array[1])

        if 'reject' in received_data['coin1']:
            last_reject1 = int(received_data['coin1']['reject'])
        else:
            last_reject1 = int(total_coin_array[2])

        received_data['coin1']['shares'] = total_coin_array[1]
        received_data['coin1']['reject'] = total_coin_array[2]

        if ( int(received_data['coin1']['shares']) > last_share1 ):
            REQUEST_COIN1_SHARES.inc( int(received_data['coin1']['shares']) - last_share1 )

        if ( int(received_data['coin1']['reject']) > last_reject1 ):
            REQUEST_COIN1_REJECT.inc( int(received_data['coin1']['reject']) - last_reject1 )


        total_coin_array = data['result'][4].split(';')
        received_data['coin2']['total_hashrate'] = total_coin_array[0]

        if 'shares' in received_data['coin2']:
            last_share2 = int(received_data['coin2']['shares'])
        else:
            last_share2 = int(total_coin_array[1])

        if 'reject' in received_data['coin2']:
            last_reject2 = int(received_data['coin2']['reject'])
        else:
            last_reject2 = int(total_coin_array[2])

        received_data['coin2']['shares'] = total_coin_array[1]
        received_data['coin2']['reject'] = total_coin_array[2]

        if ( int(received_data['coin2']['shares']) > last_share2 ):
            REQUEST_COIN2_SHARES.inc( int(received_data['coin2']['shares']) - last_share2 )

        if ( int(received_data['coin2']['reject']) > last_reject2 ):
            REQUEST_COIN2_REJECT.inc( int(received_data['coin2']['reject']) - last_reject2 )

        # Get Hashrates from claymore raw data
        id = 0
        for i in data['result'][3].split(';'):
            received_data['gpu'][id] = {}
            if (i == "off" ):
                received_data['gpu'][id]['hashrate1'] = 0
            else:
                received_data['gpu'][id]['hashrate1'] = i
            id+=1

        id = 0
        for i in data['result'][5].split(';'):
            if (i == "off" ):
                received_data['gpu'][id]['hashrate2'] = 0
            else:
                received_data['gpu'][id]['hashrate2'] = i
            id+=1

        # Get Temperature/Fan from claymore raw data
        tf = data['result'][6].split(';')

        for i in range (0,len(received_data['gpu'])):
            received_data['gpu'][i]['temp'] = 0
            received_data['gpu'][i]['fan']  = 0

        id = 0
        for i in range (0,len(tf)/2):
            received_data['gpu'][id]['temp'] = tf[i*2]
            received_data['gpu'][id]['fan']  = tf[(i*2)+1]
            id+=1
        
        # Mining Pool URL
        poolurl = data['result'][7].split(';')
        
        try:
            dcr_pool_url = poolurl[1]
        except Exception as e :
            dcr_pool_url = "off"
        
        eth_pool_url = poolurl[0]
        REQUEST_INFO.labels(received_data['claymore_version'],dcr_pool_url, eth_pool_url).set(1)

        # ETH accepted shares for every GPU.
        id = 0
        for i in data['result'][9].split(';'):
            received_data['gpu'][id]['eth_shares_accepted'] = i
            id+=1

        # ETH rejected shares for every GPU.
        id = 0
        for i in data['result'][10].split(';'):
            received_data['gpu'][id]['eth_shares_rejected'] = i
            id+=1
        
        # ETH invalid shares for every GPU.
        id = 0
        for i in data['result'][11].split(';'):
            received_data['gpu'][id]['eth_shares_invalide'] = i
            id+=1
        # DCR accepted shares for every GPU.
        # DCR rejected shares for every GPU.
        # DCR invalid shares for every GPU.


        # PCI bus index for every GPU.
        pci_idx = data['result'][15].split(';')
        
        #print pci
        for i in range (0,len(received_data['gpu'])):
            received_data['gpu'][i]['pci_bus_index'] = pci_idx[i]

        print received_data

        for i in range (0,len(received_data['gpu'])):
            REQUEST_GPU_TEMP.labels(i).set(received_data['gpu'][i]['temp'])
            REQUEST_GPU_FAN.labels(i).set(received_data['gpu'][i]['fan'])
            REQUEST_GPU_HR1.labels(i).set(received_data['gpu'][i]['hashrate1'])
            REQUEST_GPU_HR2.labels(i).set(received_data['gpu'][i]['hashrate2'])
            REQUEST_GPU_ETH_SHARES_ACCEPTED.labels(i).set(received_data['gpu'][i]['eth_shares_accepted'])
            REQUEST_GPU_ETH_SHARES_REJECTED.labels(i).set(received_data['gpu'][i]['eth_shares_rejected'])
            REQUEST_GPU_ETH_SHARES_INVALIDE.labels(i).set(received_data['gpu'][i]['eth_shares_invalide'])
            REQUEST_GPU_PCI.labels(i).set(received_data['gpu'][i]['pci_bus_index'])

        time.sleep(sleep_time)

