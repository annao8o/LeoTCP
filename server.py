import sys
import socket
import time
from config import server_port, payload_data, frame_length

# Create server socket(IPv4, TCP)
print("111")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("222")
server_IP = sys.argv[1]
algo_name = sys.argv[2]
freeze_duration = sys.argv[3]
print(server_IP, algo_name, freeze_duration)
lost_packets = 0
total_packets = 0
remaining_time = frame_length

# Set IP address, port
try:
    server_address = (server_IP, server_port)
    server_socket.bind(server_address)
    print("bind")
except:
    print("Socket binding error")

print(f'----------------------------- {algo_name} ------------------------------------------------')
print(f'Server listening on TCP port {server_port}')
# Wait for connection
server_socket.listen(5)

# Accept incoming connection
client_socket, client_address = server_socket.accept()
print(f'Server {server_IP} port {server_port} connected with client {client_address}')
print('-----------------------------------------------------------------------------')

print(f'Freeze duration: {freeze_duration}')
try:
    duration = float(freeze_duration)
    remaining_time -= duration
    print("remaining time:", remaining_time)
except:     ## if freeze_duration == None
    pass

start_time = time.time()
while True: 
    if time.time() - start_time > remaining_time:
        client_socket.close()
        break
    total_packets += 1
    ack_data = None
    try:
        client_socket.send(payload_data.encode())
        ack_data = client_socket.recv(1024).decode()
    except socket.error:
        lost_packets += 1
        # break

end_time = time.time()
client_socket.close()

data_size = len(payload_data.encode())
elapsed_time = end_time - start_time
throughput = (data_size * 8)*(total_packets-lost_packets) / (elapsed_time * 10**6)
loss_rate = lost_packets/total_packets

print(f'Timestamp: {time.time()}')
print(f'Packet Size: {len(payload_data)}')
print(f"Throughput: {throughput} Mbps")
print(f"Total Packet: {total_packets} / Lost Packet: {lost_packets}")
print(f'Packet Loss Rate: {loss_rate}')
print(f'Congestion Window (cwnd): ')