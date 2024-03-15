import sys
import socket
import threading
import traceback
import logging
import time
import csv
from config import server_port, payload_data, frame_length

throughputs = []

def handle_client(client_socket, client_address, results_filename, client_number, lock):
    logging.info(f'[+] accept connection: {client_address}')
    lost_packets = 0
    total_packets = 0
    data_transferred = 0
    start_time = time.time()

    '''
    packet_interval = 0.1       ## 100ms 간격으로 데이터 전송
    while True:
        current_time = time.time()
        if current_time < freeze_end_time:
            # logging.info(f"[+] freeze... ")
            continue
        elif current_time > fin_time:
            break
        else:
            try:
                client_socket.send(payload_data.encode())
                data_transferred += len(payload_data)
                logging.info(f"[+] send data")

                total_packets += 1
                ack_data = client_socket.recv(1024).decode()
                if not ack_data:
                    lost_packets += 1
            except socket.error:
                # logging.info(f"Connection with {client_address} lost: {e}")
                pass
    '''
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
                pass

    client_socket.close()
    # end_time = time.time()

    # total_time = end_time - start_time
    throughput = (data_transferred * 8) / (frame_length * 1024 * 1024)  # Mbps
    packet_loss_rate = (lost_packets / total_packets) * 100 if total_packets > 0 else 0

    with lock:
        throughputs.append(throughput)

    # logging.info(f"[!] {client_address} - Total packets: {total_packets}, Lost packets: {lost_packets}")
    logging.info(f"[!] {client_address} - Throughput: {throughput:.2f} Mbps, Packet Loss Rate: {packet_loss_rate:.2f}%")

    with open(results_filename, mode='a', newline='') as file:  # 'a' mode: 파일에 내용 추가
        writer = csv.writer(file)
        writer.writerow([client_number, client_address[0], f"{throughput:.2f}", f"{packet_loss_rate:.2f}"])

def calculate_average_throughput():
    if throughputs:
        return sum(throughputs) / len(throughputs)
    else:
        return 0
    
def main(server_ip, algorithm):
    result_filename = f'log/server/results_{algorithm}.csv'
    lock = threading.Lock()
    
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
            threads = []
            while True:
                client_socket, client_address = server_socket.accept()
                client_number += 1
                t = threading.Thread(target=handle_client, args=(client_socket, client_address, result_filename, client_number, lock))
                threads.append(t)
                t.start()

            # for t in threads:
            #     t.join()

        except KeyboardInterrupt:
            logging.info("\nstop server...")
        finally:
            server_socket.close()

    except Exception as e:
        logging.info(f"Exception occurred: {e}")
        traceback.print_exc()
    finally:
        average_throughput = calculate_average_throughput()
        logging.info(f"Average Throughput: {average_throughput:.2f} Mbps")

if len(sys.argv) > 2:
    srcIP = sys.argv[1]
    algorithm = sys.argv[2]
    logging.basicConfig(filename=f'log/server/server_{algorithm}.log', level=logging.DEBUG, format='%(message)s')
    main(srcIP, algorithm)
else:
    logging.info("Error: No IP address provided.")