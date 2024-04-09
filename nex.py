import os
import sys
import time
import signal
import scipy.io as scio
import csv
from mininet.net import Mininet
from mininet.link import TCLink, TCIntf
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel
from config_new import *
from utility_new import *
import psutil
log_index=0
class Mytopo( Topo ):
    def __init__(self, ):
        Topo.__init__(self)

        # Add ground user
        gs = self.addHost('gs', ip=gs_ip_addr+subnet_mask)
        
        # Add switches
        switch0 = self.addSwitch('switch0')
        self.addLink(gs, switch0, cls=TCLink)

class Algorithm:
    def __init__(self, name, is_freeze, freeze_duration=None):
        self.name = name
        self.is_freeze = is_freeze
        self._freeze_duration = freeze_duration
        self._loss_rate = None
        self._packet_delay = None

    def get_freeze_duration(self, ):
        return self._freeze_duration
    
    def set_freeze_duration(self, duration):
        self._freeze_duration = duration    

    def record_result(self, delay, loss):
        self._packet_delay.append(delay)
        self._loss_rate.append(loss)

    def get_result(self):
        return self._packet_delay, self._loss_rate
    
def activate_server(net, algo, link_bw, link_tr=None):
    gs = net.getNodeByName('gs')
    gs.cmd(f'python3.8 server_new.py {gs.IP()} {algo.name} {algo.get_freeze_duration()} {link_bw} {log_index}&')
    time.sleep(2)


def transfer_tcp_data(sat, algo, process_duration):
    pid=None
    while True:
        try:
            pid=sat.cmd(f'python3.8 client_new.py {gs_ip_addr} {sat.IP()} {algo.name} {process_duration} {log_index}&')
            pid =int(pid.split()[-1].strip())
            while psutil.pid_exists(pid):
                continue
            break
        except:
            pass
    
def update_mininet(net, link_bw, new_sat_id, old_sat_id=None):
    switch0 = net.getNodeByName("switch0")

    ### Old sat - Delete link and host
    if old_sat_id != 'NULL':    # for 0th cycle
        old_sat = net.getNodeByName("s%s"%old_sat_id)
        net.delLinkBetween(switch0, old_sat)
        net.delHost(old_sat)
    
    ### New sat - Add new Host and Link
    new_ip=ipAdd(new_sat_id)+subnet_mask
    new_sat=net.addHost("s%s"%new_sat_id, intf=TCIntf, ip=new_ip)
    net.addLink("s%s"%new_sat_id, switch0, 
                    cls=TCLink, 
                    bw = link_bw, 
                    delay = link_delay, 
                    max_queue_size=switch_queue_size)
    new_sat.setIP(new_ip)

    # Restart switch0 to apply new hosts
    switch0.start(net.controllers)

    return new_sat

def process_handover(net, gs_data, algo, link_bw, link_tr=None):
    for cycle in range(len(gs_data)):  
        print(f"\n------------------------ Cycle {cycle} / {len(gs_data)}------------------------")
    
        curr_data = gs_data[cycle]
        old_sat_id = curr_data[0].strip()
        new_sat_id = curr_data[1].strip()
        duration = curr_data[2].strip()

        # Cannot handover
        if new_sat_id == old_sat_id: # ["NULL", "NULL", "NULL"], same with (old_sat_id == "NULL")
            print("turn off the link due to lack of target statellite", end="")
            continue
        
        # Clear Old Sat & Build New Sat
        new_sat = update_mininet(net, link_bw, new_sat_id, old_sat_id)
        
        if 'proposed' in algo.name:
            algo.set_freeze_duration(float(duration))
            
        if algo.is_freeze:
            freeze_duration= algo.get_freeze_duration()
            # process_duration = frame_length - freeze_duration
            transfer_tcp_data(new_sat, algo, process_duration)
            time.sleep(freeze_duration)
        
        """
        else: # Reqest-2
        """

def run_simulation(gs_data, algo, link_bw, link_tr=None):
    my_topo = Mytopo()
    net = Mininet(topo=my_topo, link=TCLink, cleanup=True, ipBase='10.0.0.0/16')
    
    print("Start the network...")
    net.start()

    activate_server(net, algo, link_bw, link_tr)
    process_handover(net, gs_data, algo, link_bw)

    net.stop()
    print("Simulation is successfully completed!")

    throughput, loss = calculate_averages(algo.name,log_index,link_bw)
    return throughput, loss

def main():
    # -------------------------------------------Value-------------------------------------------
    # Freezed,DR,BW,TR=0
    # with open(f"{log_dir}/{log_index}/Simulation_setting", 'w') as file:
    #     file.write(f"Is Freese:\t\t{Freezed}")
    #     file.write(f"Freeze Duration:\t\t{DR}")
    #     file.write(f"Bandwidth:\t\t{BW}")
    #     file.write(f"Transmission Rate:\t\t{TR}")
    # -------------------------------------------DATA-------------------------------------------
    # Load "handover_info_file.mat"
    gs_id = 0
    file_path = os.path.join(save_file_dir, sys.argv[1])

    try:
        handover_info = scio.loadmat(file_path)
        gs_data = handover_info[str(gs_id)]
    except Exception as exception:
        print(f"Error processing file {file_path}: {exception}")

    # -------------------------------------------Simulation-------------------------------------------
    # Based on Freeze_Duration
    for f in range(11):
        freeze_duration=f*0.1
        if freeze_duration == 0.7: continue
        algo = Algorithm(f"satcp_{freeze_duration}_cwnd", is_freeze=True, freeze_duration=freeze_duration)
        # Based on BW
        bandwidth_th_loss= {}   # { BW, Values(avg troughput, avg loss) }

        #   {start_bw, end_bw, step_bw} from config.py
        for link_bw in range(start_bw, end_bw + 1, step_bw):
            average_throughput, average_loss = run_simulation(gs_data, algo, link_bw, link_tr=None)
            bandwidth_th_loss[link_bw] = (average_throughput, average_loss)
            """    
            # Based on Transmission Rate
            transrate_th_loss= {}   # { TR, Values(avg troughput, avg loss) }
            
            #   {start_tr, end_tr, step_tr} from config.py
            for link_tr in range(start_tr, end_tr + 1, step_tr):
                average_throughput, average_loss = run_simulation(gs_data, ip_addr_list, algo, link_bw, link_tr)
                transrate_th_loss[link_tr] = (average_throughput, average_loss)
            """

            # -------------------------------------------Result-------------------------------------------
            # Store simulation result as CSV
            #   {Algorithm, Bandwidth, Avg Troughput, Avg Loss}
        results_file=f"{log_dir}/{log_index}/result/result_{freeze_duration}.csv"
        try: 
            with open(results_file, mode='r') as file:
                pass

        except FileNotFoundError:
            with open(results_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Algorithm Name','Bandwidth (Mbps)', 'Average Throughput(Mbps)', 'Average Loss Rate (%)'])

        with open(results_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            for bw, values in bandwidth_th_loss.items():
                writer.writerow([algo.name, bw, values[0], values[1]])

        print(f"Results have been saved to {results_file}.")

if __name__ == '__main__':
    setLogLevel('info') # mininet log

    if len(sys.argv) != 2:
        print("need to specify the satellite position file!")
        exit()
    
    log_index=get_unique_log_index()

    main()
