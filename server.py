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

    packet_interval = 0.1       ## 100ms 간격으로 데이터 전송

    while True:
        curr_time = time.time()
        if curr_time - start_time > frame_length:
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
            # time.sleep(packet_interval)     # 다음 패킷 전송까지 대기

    client_socket.close()
    end_time = time.time()

    total_time = end_time - start_time
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