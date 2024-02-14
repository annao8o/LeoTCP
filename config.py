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
frame_length = 1
payload_data = "Hello, this is your data payload!"
switch_queue_size = 50000
link_bw = 200       # Mbps
# a negligible delay value assigned to links when the simulation has not started yet
link_delay = '0.01ms'

satellites_num = 6000
gs_ip_addr = '10.0.1.100/16'
base_ip='10.0.0.0'
subnet_mask='/16'
server_port = 12345


## File settings
data_file_dir = './data/'
save_file_dir = './save/'
ground_station_file_name = 'ground_stations.xlsx'
handover_info_file_name = 'handover_info_file.mat'
server_output_path = 'log/log_server.txt'