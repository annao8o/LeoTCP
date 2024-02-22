import sys
import socket
import time
import logging
from config import server_port, frame_length


def main(server_ip, client_ip, algorithm, duration, remaining_time):
    logging.info(f"---------------------- {algorithm} -----------------------------")
    try:
        duration = float(duration)
        remaining_time -= duration
        logging.info(f'remaining time: {remaining_time}')
    except:     ## if freeze_duration == None
        pass

    # create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connect to server
        client_socket.connect((server_ip, server_port))
        logging.info(f"[+] {algorithm} {client_ip} is connected to server {server_ip}:{server_port}.")
        start_time = time.time()
        packet_num = 0

        while True:
            # receive data from server
            data = client_socket.recv(1024)
            if not data:
                break
            client_socket.sendall('ACK'.encode()) 
            packet_num += 1
            if time.time() - start_time > remaining_time:
                client_socket.close()
                break
    except ConnectionRefusedError:
        logging.info(f"[-] cannot connected to {server_ip}:{server_port}.")
    except KeyboardInterrupt:
        logging.info("\n[-] Connection is interrupted.")
    finally:
        logging.info(f'{client_ip} received {packet_num} packets.')
        logging.info(f'[-] {client_ip} connection is closed..')
        client_socket.close()

server_ip = sys.argv[1]
client_ip = sys.argv[2]
algorithm = sys.argv[3]
duration = sys.argv[4]
remaining_time = frame_length
logging.basicConfig(filename=f'log/client/client_{algorithm}.log', level=logging.DEBUG, format='%(message)s')
main(server_ip, client_ip, algorithm, duration, remaining_time)


'''
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
'''