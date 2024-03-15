import sys
import socket
import time
import logging
import argparse
from config import server_port, frame_length


def main(server_ip, client_ip, algorithm, mode, duration):
    logging.basicConfig(filename=f'log/client/client_{algorithm}.log', level=logging.DEBUG, format='%(asctime)s - %(message)s')
    logging.info(f"Starting client with mode {mode} for duration {duration} seconds")

    duration = float(duration)
    logging.info(duration)
    # create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    packet_num = 0

    try:
        # connect to server
        client_socket.connect((server_ip, server_port))
        logging.info(f"[+] {algorithm} {client_ip} is connected to server {server_ip}:{server_port}.")
        start_time = time.time()
        end_time = start_time + duration

        if mode == 'old':
            time.sleep(duration)
        else:
            while True:
                # receive data from server
                data = client_socket.recv(1024)
                client_socket.sendall('ACK'.encode()) 
                packet_num += 1
                if time.time() > end_time:
                    break
    except ConnectionRefusedError:
        logging.info(f"[-] cannot connected to {server_ip}:{server_port}.")
    except KeyboardInterrupt:
        logging.info("\n[-] Connection is interrupted.")
    finally:
        logging.info(f'{client_ip} received {packet_num} packets.')
        logging.info(f'[-] {client_ip} connection is closed..')
        client_socket.close()

    '''
    try:
        # connect to server
        client_socket.connect((server_ip, server_port))
        logging.info(f"[+] {algorithm} {client_ip} is connected to server {server_ip}:{server_port}.")
        client_socket.send(str(freeze_duration).encode())      ## send information of freeze duration
        start_time = time.time()

        while True:
            try: 
                data = client_socket.recv(1024)
                logging.info(f"receives data {len(data)}.")
                client_socket.sendall('ACK'.encode())
                packet_num += 1
            except:
                pass
            # if current_time > end_time:
            #     client_socket.close()
            #     break
    except ConnectionRefusedError:
        logging.info(f"[-] cannot connected to {server_ip}:{server_port}.")
    except KeyboardInterrupt:
        logging.info("\n[-] Connection is interrupted.")
    finally:
        logging.info(f'{client_ip} received {packet_num} packets.')
        logging.info(f'[-] {client_ip} connection is closed..')
        client_socket.close()
    '''

parser = argparse.ArgumentParser(description='Client for Mininet simulation.')
parser.add_argument('server_ip', type=str, help='Server IP address')
parser.add_argument('client_ip', type=str, help='Client IP address')
parser.add_argument('algorithm', type=str, help='Algorithm name')
parser.add_argument('--mode', type=str, choices=['old', 'new'], help='Operation mode')
parser.add_argument('duration', type=float, help='Duration in seconds')
args = parser.parse_args()

main(args.server_ip, args.client_ip, args.algorithm, args.mode, args.duration)

# server_ip = sys.argv[1]
# client_ip = sys.argv[2]
# algorithm = sys.argv[3]
# state = sys.argv[4]
# duration = sys.argv[5]
# logging.info(f"{server_ip} {client_ip} {algorithm} {state} {duration}")
# logging.basicConfig(filename=f'log/client/client_{algorithm}.log', level=logging.DEBUG, format='%(message)s')
# main(server_ip, client_ip, algorithm, state, duration)