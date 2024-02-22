import subprocess
import time
import os
import sys
import scipy.io as scio
import ipaddress
import csv
from config import *
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.node import RemoteController

kernel_output = open('/dev/kmsg', 'w')

class Mytopo( Topo ):
    def __init__(self, addr_list, init_sat):
        Topo.__init__(self)
        self.address_list = addr_list

        # Add ground user
        gs = self.addHost('gs', ip=gs_ip_addr)

        # Add satellite
        self.addHost(f's{init_sat}', ip=f'{addr_list[int(init_sat)]}')

        # Add switches
        switch0 = self.addSwitch('switch0')

        # Create links
        self.addLink(gs, switch0, cls=TCLink)
        self.addLink("s%s" % init_sat, switch0, cls=TCLink)    

class Algorithm:
    def __init__(self, name, is_freeze, freeze_duration=None) -> None:
        self.name = name
        self.is_freeze = is_freeze
        self.freeze_duration = None
        self.loss_rate = None
        self.packet_delay = None

        if freeze_duration:
            self.set_freeze_duration(freeze_duration)

    def set_freeze_duration(self, duration):
        self.freeze_duration = duration

    def record_result(self, delay, loss):
        self.packet_delay.append(delay)
        self.loss_rate.append(loss)

    def get_result(self):
        return self.packet_delay, self.loss_rate

def remove_satellite(net, node1, node2):
    ## break link 
    try:
        net.configLinkStatus('switch0', node1.name, 'down')
        interfaces = node1.connectionsTo(node2)
        node1_intf = interfaces[0][0]
        node2_intf = interfaces[0][1]
        node1.delIntf(node1_intf)
        node2.delIntf(node2_intf)
    except Exception as e:
        print(f"failed to break link with {node1.name} and {node2.name}")

    ## delete node
    net.delNode(node1)
    print(f"Delete node {node1.name}...")

def add_satellite(net, switch, new_node, address):
    host = net.addHost(f's{new_node}')
    # CLI(net)
    net.addLink(host, switch, cls=TCLink)
    set_link_properties(net, host, switch, bw=link_bw, delay=link_delay, switch_queue_size=switch_queue_size)
    host.intfList()[0].setIP(address)
    return host
    
def set_link_properties(net, node1, node2, bw, delay, switch_queue_size):
    print(f"Set the properties of link between {node1} and {node2}")
    interfaces = node1.connectionsTo(node2)
    src_intf = interfaces[0][0]
    dst_intf = interfaces[0][1]
    src_intf.config(bw = bw, delay = delay, max_queue_size=switch_queue_size, smooth_change = True)
    dst_intf.config(bw = bw, delay = delay, max_queue_size=switch_queue_size, smooth_change = True)
    
def allocate_ip_addresses(num_satellites, base_ip="10.0.0.0", subnet_mask="/16"):
    base_network = ipaddress.IPv4Network(base_ip + subnet_mask, strict=False)
    allocated_ips = []
    for i in range(num_satellites):
        satellite_ip = str(base_network.network_address + i)
        allocated_ips.append(satellite_ip + subnet_mask)

    return allocated_ips

def simulate_handover(net, gs, curr_sat, target_sat, duration):
    try:
        # subprocess.run(["echo", "UNIX TIME: %s: end handover triggered!" % str(time.time())], stdout=kernel_output)
        # Handover Starts
        net.configLinkStatus(gs, curr_sat, 'down')
        time.sleep(duration)
        net.configLinkStatus(gs, target_sat, 'up')
        # Handover ends
    except Exception as e:
        print("failed to simulate end handover:", e)

def tcp_data_transfer(src, dst, algorithm, duration):
    print(f"Starting TCP data transfer from {src.name} to {dst.name}")
    dst.cmd(f'python3.8 client.py {src.IP()} {dst.IP()} {algorithm} {duration} &')

def show_results(algo_list, result_file):
    with open(result_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Algorithm", "delay", "loss"])
    
    # Write data for each algorithm
    for algo in algo_list:
        algo_delay, algo_loss = algo.get_result()
        for i in range(len(algo_delay)):
            writer.writerow([algo.name, algo_delay[i], algo_loss[i]])

    print("Result csv file is generated successfully!")
            
def process_handover(net, address_list, algo_list, ho_info):
    gs = net.getNodeByName('gs')
    switch = net.getNodeByName('switch0')

    for cycle in range(1, len(ho_info)):
        print(f"\n------------------------ Cycle {cycle} / {len(ho_info)}------------------------")
        tstart = time.time()
        curr_data = gs_data[cycle]
        curr_sat = curr_data[0].strip()

        if curr_sat == "NULL":
            net.configLinkStatus('s%s' % curr_sat, 'switch0', 'down')
            print("turn off the link due to lack of target statellite")
            time.sleep(frame_length)
            continue
        else:
            target_sat = curr_data[1].strip()
            duration = float(curr_data[2].strip())
            if curr_sat != target_sat:
                old_sat = net.getNodeByName(f's{curr_sat}')
                addr = address_list[int(target_sat)]
                net.configLinkStatus('switch0', old_sat.name, 'down')
                remove_satellite(net, old_sat, switch)
                new_sat = add_satellite(net, switch, target_sat, addr)
                for algo in algo_list:
                    ## Freeze == True 인 알고리즘들은 freeze duration 동안 data 보내지 않음
                    if algo.is_freeze:
                        if not algo.freeze_duration:
                            algo.set_freeze_duration(duration)
                            # time.sleep(algo.freeze_duration)
                        # simulate_handover()
                    else: 
                        tcp_data_transfer(gs, old_sat, algo.name, algo.freeze_duration)

                    ## 나머지 duration 동안 data 전송 
                    ## Transmit data to the new satellite
                    tcp_data_transfer(gs, new_sat, algo.name, algo.freeze_duration)
                
        # -------------------------------------------------------------------------------------
        # sleep for extra time to reach one cycle duration
        tend = time.time()
        sleep_duration = frame_length - (tend - tstart)
        if sleep_duration < 0:
            sleep_duration = 0
        print("sleep duration:", sleep_duration)
        time.sleep(sleep_duration)

    # show_results(algo_list)


if __name__ == '__main__':
    setLogLevel('info')

    if len(sys.argv) != 2:
        print("need to specify the satellite position file!")
        exit()
    
    gs_id = 0
    file_path = os.path.join(save_file_dir, sys.argv[1])
    try:
        handover_info = scio.loadmat(file_path)
        gs_data = handover_info[str(gs_id)]
    except Exception as exception:
        # Handle exceptions (you may want to log or print the exception)
        print(f"Error processing file {file_path}: {exception}")

    # Generate ip address for each satellite
    ip_address_list = allocate_ip_addresses(satellites_num, base_ip=base_ip, subnet_mask=subnet_mask)

    # Add algorithms
    algorithm_list = []

    ## Proposed
    # algo = Algorithm("proposed", is_freeze=True)
    # algorithm_list.append(algo)

    ## SaTCP - 0.6
    # algo = Algorithm("satcp", is_freeze=True, freeze_duration=0.6)
    # algorithm_list.append(algo)

    ## SaTCP - 0.4
    # algo = Algorithm("satcp_0.4", is_freeze=True, freeze_duration=0.4)
    # algorithm_list.append(algo)

    ## No freeze
    algo = Algorithm("noFreeze", is_freeze=False)
    algorithm_list.append(algo)


    # Configure initial topology
    init_sat = gs_data[0][1].strip()    # ['NULL', sat_id, 'NULL']
    my_topo = Mytopo(ip_address_list, init_sat)
    net = Mininet(topo=my_topo, link=TCLink)

    # Initialize link between switch and inital satellite
    print("start the network...")
    net.start()

    gs = net.getNodeByName('gs')
    print(gs, gs.IP())
    gs.cmd(f'python3.8 server.py {gs.IP()} {algo.name} &')
    time.sleep(2)
    # gs.cmd(f'iperf -s -p {server_port} -i 1> log_server.txt &')    # 2000 (Bytes)

    # bgproc = gs.cmd(f'ps ef')
    # print(bgproc)

    sat = net.getNodeByName('s%s' % init_sat)
    switch = net.getNodeByName('switch0')
    set_link_properties(net, sat, switch, link_bw, link_delay, switch_queue_size=switch_queue_size)
    # sat.cmd(f'python3.8 client.py {gs.IP()} >> log/log_client.txt')
    # sat.cmd(f'iperf -c {gs.IP()} -p {server_port} -t 20 > log_client.txt &')
    for algo in algorithm_list:
        tcp_data_transfer(gs, sat, algo.name, duration=0)
    
    process_handover(net, ip_address_list, algorithm_list, gs_data)
    CLI(net)

    net.stop()
    print("Simuliation is successfully completed!")