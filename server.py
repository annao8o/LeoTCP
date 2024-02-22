import sys
import socket
import threading
import traceback
import logging
import time
import csv
from config import server_port, payload_data, frame_length

def handle_client(client_socket, client_address, results_filename, client_number):
    logging.info(f'[+] accept connection: {client_address}')
    lost_packets = 0
    total_packets = 0
    data_transferred = 0
    start_time = time.time()
    while True:
        current_time = time.time()
        if current_time - start_time > frame_length:
            break
        else:
            try:
                client_socket.send(payload_data.encode())
                total_packets += 1
                data_transferred += len(payload_data)
                ack_data = client_socket.recv(1024).decode()
                if not ack_data:
                    lost_packets += 1
            except socket.error:
                # lost_packets += 1
                pass

    client_socket.close()
   
    total_time = current_time - start_time
    throughput = (data_transferred * 8) / (total_time * 1024 * 1024)  # Mbps
    packet_loss_rate = (lost_packets / total_packets) * 100 if total_packets > 0 else 0

    logging.info(f"[-] connection is stopped: {client_address}")
    logging.info(f"[!] {client_address} - Total packets: {total_packets}, Lost packets: {lost_packets}")
    logging.info(f"[!] {client_address} - Throughput: {throughput:.2f} Mbps, Packet Loss Rate: {packet_loss_rate:.2f}%")

    with open(results_filename, mode='a', newline='') as file:  # 'a' mode: 파일에 내용 추가
        writer = csv.writer(file)
        writer.writerow([client_number, client_address[0], f"{throughput:.2f}", f"{packet_loss_rate:.2f}"])

def main(server_ip, algorithm):
    result_filename = f'log/server/results_{algorithm}.csv'
    with open(result_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Number', 'Client Address', 'Throughput (Mbps)', 'Packet Loss Rate (%)'])
    
    try:
        # create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind server socket
        server_socket.bind((server_ip, server_port))
        logging.info(f'\n[*] start server {server_ip}:{server_port}.')

        # wait for connection
        server_socket.listen(5)
        # logging.info('waiting...')

        try:
            client_number = 0
            while True:
                # accept the connections from clients
                client_socket, client_address = server_socket.accept()
                client_number += 1
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, result_filename, client_number))
                client_thread.start()
        except KeyboardInterrupt:
            logging.info("\nstop server...")
        finally:
            server_socket.close()
    except Exception as e:
        logging.info(f"Exception occurred: {e}")
        traceback.print_exc()


if len(sys.argv) > 1:
    srcIP = sys.argv[1]
    algorithm = sys.argv[2]
    logging.basicConfig(filename=f'log/server/server_{algorithm}.log', level=logging.DEBUG, format='%(message)s')
    main(srcIP, algorithm)
else:
    logging.info("Error: No IP address provided.")


'''
# def handle_client(client_socket, client_address):
#     print(f'[+] accepted connection: {client_address}')
    
#     while True:
#         client_socket.sendall(payload_data)
#         ack_data = client_socket.recv(1024).decode()
#         if not ack_data:
#             break
    
#     print(f"[-] connection is stopped: {client_address}")
#     client_socket.close()
    
server_ip = sys.argv[1]

# create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind server socket
server_socket.bind((server_ip, server_port))
print(f"[*] start server {server_ip}:{server_port}.")

try:
    while True:
        # wait for connection
        server_socket.listen(10)

        # accept the connections from clients
        client_socket, client_address = server_socket.accept()
        print(f'[+] accepted connection: {client_address}')
        packet_num = 0
        while True:
            client_socket.sendall(payload_data)
            ack_data = client_socket.recv(1024)
            if ack_data:
                packet_num += 1
            # if not ack_data:
            if packet_num > 5:
                print(f"[-] connection is stopped: {client_address}")
                client_socket.close()
                break
        # client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        # client_thread.start()
except KeyboardInterrupt:
    print("\nstop server...")
finally:
    server_socket.close()
'''

'''
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
'''