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

def add_satellite(net, link_bw, switch, new_node, address):
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

def tcp_data_transfer(net, src, dst, algo, duration):
    print(f"Starting TCP data transfer from {src.name} to {dst.name}")
    print(src.IP(), dst.IP())
    dst.cmd(f'python3.8 client.py {src.IP()} {dst.IP()} {algo.name} {duration} &')
    if not algo.is_freeze:
        net.configLinkStatus('switch0', dst.name, 'down')

def process_handover(net, link_bw, address_list, algo, gs_data):
    gs = net.getNodeByName('gs')
    switch = net.getNodeByName('switch0')

    for cycle in range(1, len(gs_data)):
        print(f"\n------------------------ Cycle {cycle} / {len(gs_data)}------------------------")
        curr_data = gs_data[cycle]
        curr_sat = curr_data[0].strip()
        
        if curr_sat == "NULL":
            # net.configLinkStatus('s%s' % curr_sat, 'switch0', 'down')
            print("turn off the link due to lack of target statellite")
            time.sleep(frame_length)
            continue

        else:
            target_sat = curr_data[1].strip()
            target_addr = address_list[int(target_sat)]
            # if curr_sat == target_sat:
            #     continue
            if curr_sat != target_sat:
                old_sat = net.getNodeByName(f's{curr_sat}')

                tstart = time.time()
                if algo.is_freeze:
                    if 'proposed' in algo.name:
                        duration = float(curr_data[2].strip())
                        algo.set_freeze_duration(duration)
                    
                    ## set new environment 
                    net.configLinkStatus('switch0', old_sat.name, 'down')
                    remove_satellite(net, old_sat, switch)
                    new_sat = add_satellite(net, link_bw, switch, target_sat, target_addr)

                    # ## freeze and send data
                    time.sleep(algo.freeze_duration)
                    remaining_time = frame_length - algo.freeze_duration
                    print(frame_length, algo.freeze_duration, remaining_time)
                    tcp_data_transfer(net, gs, new_sat, algo, remaining_time)
                else:
                    # net.configLinkStatus('switch0', old_sat.name, 'down')
                    tcp_data_transfer(net, gs, old_sat, algo, frame_length)
                    time.sleep(1)
                    remove_satellite(net, old_sat, switch)
                    new_sat = add_satellite(net, switch, target_sat, target_addr)
                    # 전체 한 cycle의 duration_per_cycle - handover_duration 을 한 나머지는 새로운 satellite에 data 전송하기

        time.sleep(1)

def main_simulation(link_bw):
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

    # Proposed
    # algo = Algorithm("proposed", is_freeze=True)

    # SaTCP - 0.3
    algo = Algorithm("satcp_0.3", is_freeze=True, freeze_duration=0.3)

    # SaTCP - 0.9
    # algo = Algorithm("satcp_0.9", is_freeze=True, freeze_duration=0.9)

    # # No freeze
    # algo = Algorithm("noFreeze", is_freeze=False)
    # algorithm_list.append(algo)

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
    
    tcp_data_transfer(net, gs, sat, algo, duration=0)
    
    process_handover(net, link_bw, ip_address_list, algo, gs_data)
    # CLI(net)

    net.stop()
    print("Simulation is successfully completed!")

    throughput, loss = calculate_averages(f'log/server/results_{algo.name}.csv')
    return algo.name, throughput, loss

# Function to calculate average throughput and loss from CSV data
def calculate_averages(csv_file_path):
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        
        # Initialize variables to calculate sums
        total_throughput = 0
        total_loss = 0
        row_count = 0

        # Iterate through each row in the CSV file
        for row in csv_reader:
            total_throughput += float(row["Throughput (Mbps)"])
            total_loss += float(row["Packet Loss Rate (%)"])
            row_count += 1

        # Calculate averages
        average_throughput = total_throughput / row_count
        average_loss = total_loss / row_count

        return average_throughput, average_loss


if __name__ == '__main__':
    setLogLevel('info')

    if len(sys.argv) != 2:
        print("need to specify the satellite position file!")
        exit()
    
    bandwidth_throughput = {}
    bandwidth_loss = {}

    for link_bw in range(start_bw, end_bw + 1, step_bw):
        algo_name, average_throughput, average_loss = main_simulation(link_bw)
        bandwidth_throughput[link_bw] = (average_throughput, average_loss)
    
    try: 
        with open(results_file, mode='r') as file:
            pass
    except FileNotFoundError:
        with open(results_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Algorithm Name', 'Bandwidth (Mbps)', 'Average Throughput(Mbps)', 'Average Loss Rate (%)'])

    with open(results_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        for bw, values in bandwidth_throughput.items():
            writer.writerow([algo_name, bw, values[0], values[1]])
            print(f"Bandwidth: {bw} Mbps, Average Throughput: {values[0]} Mbps, Average Loss: {values[1]}")

    print(f"Results have been saved to {results_file}.")
