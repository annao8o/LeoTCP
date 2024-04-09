f_c = 20e9  # Carrier frequency in Hz            # Ref: A Successive Deep Q-Learning ~
H_i = 1  # RSS for LoS link (in dB)
h_i = 20  # RSS for NLoS link (in dB)
a = 12.08  # Environment dependent constant
b = 0.21  # Environment dependent constant
phi = 0.2  # Amplitude scintillation index
X = 5  # Determined by building type
Y = 10  # Determined by UT location
Z = 15  # Determined by carrier frequency
R = 6378 * (10 ** 3)  # Earth radius in meters  # Ref: SaTCP
c = 3e8  # Speed of light in meters/second
communication_range = 1000  # Communication range in meters

## Handover settings
ho_threshold = 1    # [0,1,2,3,4,5] Ref: CL Effect of channel fading ~ 
hof_threshold = 0.5
m = 1   # [1,3,5] Ref: CL Effect of channel fading ~ 
max_duration = 10

## TCP settings
REMOTE_CONTROLLER_IP = "127.0.0.1"
frame_length = 5
max_handover_time = 1
payload_size = 1024     # 5KB [SaTCP]
payload_data = "A" * payload_size      
switch_queue_size = 50000
# link_bw = 100       # Mbps
start_bw = 100
end_bw = 1000
step_bw = 100
link_delay = '0.01ms'

satellites_num = 6000
gs_ip_addr = '10.0.33.100'
base_ip='10.0.0.0'
subnet_mask='/16'
server_port = 12345

sub_mask=16
ipBaseNum=167772161

## File settings
data_file_dir = './data/'
save_file_dir = './save/'
ground_station_file_name = 'ground_stations.xlsx'
handover_info_file_name = 'handover_info_file.mat'
results_file = './save/results.csv'
result_log_dir = "./log/result/"
server_log_dir = "./log/server/"
client_log_dir = "./log/client/"

# SI
start_tr = 10
end_tr = 100
step_tr = 10

time_frame_length= 5
process_duration=4
log_dir="./log"
base_dir = log_dir

# SI