import sys
import socket
import time
from config import server_port, frame_length

start_time = time.time()
num_data = 0

# Create clinet socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_IP = sys.argv[1]
algo_name = sys.argv[2]

# Set server IP & port
server_address = (server_IP, server_port)

# Connect to server
client_socket.connect(server_address)
clinet_ip = client_socket.getsockname()
print(f'------------------------------- {algo_name} ----------------------------------------------')
print(f'Client {clinet_ip} is connected to server: {server_address}')
print('-----------------------------------------------------------------------------')

while True:
    if time.time() - start_time > frame_length:
        client_socket.close()
        break

    # Receive data from server
    data = client_socket.recv(1024).decode()
    num_data += 1

    if data:
        # Send ack to server
        ack = "Received data"
        client_socket.sendall(ack.encode())

print(f"Received data: {num_data}")