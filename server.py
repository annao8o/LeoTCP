import sys
import socket
import threading
from threading import Lock
import traceback
import logging
import time
import csv
import os
from config import server_port, payload_data, frame_length

def handle_client(client_socket, client_address, results, lock):
    logging.info(f'[+] accept connection: {client_address}')
    lost_packets = 0
    total_packets = 0
    data_transferred = 0
    start_time = time.time()
    last_interval_time = start_time
    interval_data_transferred = 0

    throughput_records = []

    while True:
        curr_time = time.time()
        if curr_time - start_time > frame_length:
            break
        else:
            try:
                client_socket.send(payload_data.encode())
                data_transferred += len(payload_data)
                interval_data_transferred += len(payload_data)
                total_packets += 1
                ack_data = client_socket.recv(1024).decode()
                if not ack_data:
                    lost_packets += 1
            except socket.error as e:
                # logging.error(f"Socket error: {e}")
                # lost_packets += 1
                pass
            
            if curr_time - last_interval_time >= 1:
                interval_throughput = (interval_data_transferred * 8) / ((curr_time - last_interval_time) * 1024 * 1024)  # Mbps
                throughput_records.append(interval_throughput)
                interval_data_transferred = 0
                last_interval_time = curr_time

    client_socket.close()
    end_time = time.time()

    total_time = end_time - start_time
    final_throughput = (data_transferred * 8) / (total_time * 1024 * 1024)  # Mbps
    packet_loss_rate = (lost_packets / total_packets) * 100 if total_packets > 0 else 0

    with lock:
        results.append((client_address, final_throughput, packet_loss_rate))

    logging.info(f"[!] {client_address} - Throughput: {final_throughput:.2f} Mbps, Packet Loss Rate: {packet_loss_rate:.2f}%")
    for i, tp in enumerate(throughput_records):
        logging.info(f"[!] {client_address} - Throughput at second {i+1}: {tp:.2f} Mbps")

def calculate_average_throughput(results):
    total_throughput = sum(throughput for _, throughput, _ in results)
    return total_throughput / len(results) if results else 0

def calculate_packet_loss_rate(results):
    if not results:
        return 0
    total_loss_rate = sum(loss_rate for _, _, loss_rate in results)
    average_loss_rate = total_loss_rate / len(results)
    return average_loss_rate
    
def main(server_ip, algorithm, bandwidth):
    result_filename = f'log/server/results_{algorithm}.csv'
    results = []
    lock = Lock()  # 결과 리스트에 대한 접근을 동기화하기 위한 Lock 객체
    mode = 'w'  
    
    # 파일이 존재하고, 마지막으로 기록된 bandwidth 값을 확인
    if os.path.exists(result_filename):
        with open(result_filename, 'r') as file:
            last_line = file.readlines()[-1]
            last_bandwidth = last_line.split(',')[0]  # CSV 첫 번째 컬럼을 bandwidth로 가정
            if last_bandwidth == bandwidth:
                mode = 'a'  # 이전 bandwidth와 같으면 append 모드
    try:
        # create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind server socket
        server_socket.bind((server_ip, server_port))
        logging.info(f'\n[*] start server {server_ip}:{server_port}.')

        # wait for connection
        server_socket.listen(2)
        logging.info(f'[*] Server started {server_ip}:{server_port}. Waiting for connections...')

        try:
            client_number = 0
            threads = []
            while True:
                client_socket, client_address = server_socket.accept()
                client_number += 1
                t = threading.Thread(target=handle_client, args=(client_socket, client_address, results, lock))
                threads.append(t)
                t.start()
                
                if len(threads) >= 2:  # 두 클라이언트 연결 처리 설정
                    break

            # 모든 스레드의 종료를 기다림
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            logging.info("\nstop server...")
    except Exception as e:
        logging.info(f"Exception occurred: {e}")
        traceback.print_exc()
        
    average_throughput = calculate_average_throughput(results)
    logging.info(f"[!] Average Throughput: {average_throughput:.2f} Mbps")

    average_packet_loss_rate = calculate_packet_loss_rate(results)
    logging.info(f"[!] Average Packet Loss Rate: {average_packet_loss_rate:.2f}%")

    with open(result_filename, mode, newline='') as file:
        csv_writer = csv.writer(file)
        if mode == 'w':
            csv_writer.writerow(["Bandwidth", "Average Throughput (Mbps)", "Packet Loss Rate (%)"])  # 새로 쓰기 모드인 경우 헤더 추가
        csv_writer.writerow([bandwidth, f"{average_throughput:.2f}", f"{average_packet_loss_rate:.2f}"])

if __name__ == '__main__':
    if len(sys.argv) > 3:
        srcIP = sys.argv[1]
        algorithm = sys.argv[2]
        bandwidth = sys.argv[3]
        logging.basicConfig(filename=f'log/server/server_{algorithm}.log', level=logging.DEBUG, format='%(message)s')
        main(srcIP, algorithm, bandwidth)
    else:
        logging.error("Error: Insufficient arguments provided.")
