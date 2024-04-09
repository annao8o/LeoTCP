import socket
import threading
import traceback
import logging
import argparse
import time
import csv
from config_new import server_port, payload_data, payload_size, log_dir, time_frame_length
from queue import Queue

# from threading import Lock
def handle_client(client_socket, client_address, freeze_duration, result_filename):
    start_time = time.time()
    logging.info(f'[+] {client_address} is connected')
    
    lost_packets_size = 0                        # lost packet size
    transferred_packet_size = 0
    total_packets_size = 0                       # total packet size

    transferred_data_size = 0                    # transferred data size [packet_size * payload_size(5 * 1024)]

    losted= False

    # recevier
    while True:
        # Connection Timeout
        if  time_frame_length < time.time() - start_time:
            logging.info(f"[*] {client_address} is time out")
            break

        try:
            total_packets_size += 1
            client_socket.sendall(payload_data.encode())                   # send data **Caution**
            ack_data=client_socket.recv(3).decode()

            if "ACK" == ack_data:
                transferred_data_size += payload_size
                transferred_packet_size+=1
            elif "NACK" == ack_data:
                pass
            elif "END" == ack_data:
                logging.info(f"[*] {client_address} is freezed during {freeze_duration}")
                time.sleep(freeze_duration)

        except socket.error as e:
            if not losted:
                logging.warn(f"{client_address} is losting packets {e}")
                losted=True
            lost_packets_size += 1
    
    # Disconnect client socket
    client_socket.close()
    end_time = time.time()
    logging.info(f"[-] {client_address} is disconnected")

    total_time = end_time - start_time
    final_throughput = (transferred_data_size * 8 / 1024 / 1024) / total_time  # Mbps
    packet_loss_rate = (lost_packets_size / total_packets_size) * 100 if total_packets_size > 0 else 0

    logging.info(f"[*] {client_address} Transferred Data Size: {transferred_data_size}, Time: {total_time}")
    logging.info(f"[*] {client_address} Lost Packet: {lost_packets_size}, Transferred Packet: {transferred_packet_size}, Total Packet: {total_packets_size}")
    logging.info(f"[*] {client_address} - Throughput: {final_throughput:.2f} Mbps, Packet Loss Rate: {packet_loss_rate:.2f}%")

    # Store a cycle result as CSV
    with open(result_filename, 'a', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([f"{final_throughput:.2f}", f"{packet_loss_rate:.2f}"])
    logging.info(f"Store result data of client {client_address}")
    

def main(server_ip, algorithm, freeze_duration, bandwidth, log_index):
    # Result of each Bandwidth
    result_filename = f"{log_dir}/{log_index}/result/{algorithm}_{bandwidth}.csv"
    # lock = Lock() # to synchronize result csv file

    # Create CSV file with header
    with open(result_filename, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["Average Throughput (Mbps)", "Packet Loss Rate (%)"])

    # Init socket for TCP connection
    try:
        # create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # bind server socket
        server_socket.bind((server_ip, server_port))

        # wait for connection
        server_socket.listen()

        logging.info(f"Start Server {server_ip}:{server_port}. Waiting for connections...")

    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        traceback.print_exc()
    
    # Run server without rebooting
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            t = threading.Thread(target=handle_client, args=(client_socket, client_address, freeze_duration, result_filename))
            t.start()
    
    except KeyboardInterrupt:
        logging.warn("Stop server by Keyboard Interrupt")

    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        traceback.print_exc()

    finally:
        logging.info("Stop server")
        server_socket.close()

parser = argparse.ArgumentParser(description="Server for Mininet simulation.")
parser.add_argument("server_ip", type=str, help="Server IP address")
parser.add_argument("algorithm", type=str, help="Algorithm name")
parser.add_argument("freeze_duration", type=float, help="Freeze Duration")
parser.add_argument("bandwidth", type=int, help="Bandwidth")
parser.add_argument("log_index", type=int, help="Log index",default=0)
args = parser.parse_args()

logging.basicConfig(filename=f"{log_dir}/{args.log_index}/server/{args.algorithm}_{args.bandwidth}.log", level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == '__main__':
    main(args.server_ip, args.algorithm, args.freeze_duration , args.bandwidth, args.log_index)
