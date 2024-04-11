import socket
import time
import logging
import argparse
from config_new import server_port, log_dir, payload_size
from utility_new import getHostID


def main(server_ip, client_id, process_duration):
    logging.info(f"{client_id}: is started during {process_duration} sec.")
    
    # Create socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        received_data_size = 0
        received_packet_size = 0

    except Exception as e:
        logging.error(f"{e}")

    # Connect to server
    try:
        client_socket.connect((server_ip, server_port))
        logging.info(f"[+] {client_id} is connected to server {server_ip}:{server_port}.")
        start_time = time.time()

        # Receive data from server
        while True: 
            data = client_socket.recv(payload_size).decode()
            if data:
                client_socket.send("ACK".encode()) 
                received_data_size += len(data)
                received_packet_size+=1
            else:
                client_socket.send("NACK".encode()) 

            # Timeout process time
            if process_duration < time.time()-start_time:
                logging.info(f"{client_id} END")
                client_socket.send("END".encode())
                break

    except ConnectionRefusedError:
        logging.error(f"{client_id} Cannot connected to {server_ip}:{server_port}.")
    except KeyboardInterrupt:
        logging.warn(f"{client_id} Connection is interrupted.")
    except Exception as e:
        logging.error(f"{e}")
    finally:
        logging.info(f'[-] {client_id} connection is closed.')
        logging.info(f"{client_id} received {received_data_size} datas and {received_packet_size} packets.\n")
        client_socket.close()

parser = argparse.ArgumentParser(description="Client for Mininet simulation.")
parser.add_argument("server_ip", type=str, help="Server IP address")
parser.add_argument("client_ip", type=str, help="Client IP address")
parser.add_argument("algorithm", type=str, help="Algorithm name")
parser.add_argument("process_duration", type=float, help="Process Duration in seconds")
parser.add_argument("log_index", type=int, help="Log index", default=0)
args = parser.parse_args()

logging.basicConfig(filename=f"{log_dir}/{args.log_index}/client/{args.algorithm}.log", level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == '__main__':
    client_id=(args.client_ip, getHostID(args.client_ip))
    main(args.server_ip, client_id, float(args.process_duration))