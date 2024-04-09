import networkx as nx
import math
import numpy as np
import csv
from config_new import *
import os

"""
    input: (lat, long, alt)
    output: (x, y, z)
    algorithm borrowed from StarPerf's MATLAB codes; conversion of coordinate systems
"""
def lla2cbf(position):
    pi = math.pi
    r = R + position[2]
    theta = pi / 2 - position[0] * pi / 180
    phi = 2 * pi + position[1] * pi / 180
    x = (r * math.sin(theta)) * math.cos(phi)
    y = (r * math.sin(theta)) * math.sin(phi)
    z = r * math.cos(theta)
    return (x, y, z)

def degToRad(deg):
    pi = math.pi
    return deg * pi / 180

"""
    get the ground coverage limit L of a celestial object ## 천체
    see README.md for more details
"""
def getCoverageLimitL(elevation, altitude):
    gamma = 90 - (elevation)
    l = R * math.sin(degToRad(gamma))
    theta = (180 - gamma) / 2
    d = l / (math.tan(degToRad(theta)))
    L = math.sqrt((altitude + d) ** 2 + l ** 2)
    return L

'''
    given coordinates of a satellite, a ground station, and coverage limit L, check 
    if the satellite can cover the ground station
'''
def checkSatCoverGroundStation(sat_position_cbf, gs_position_cbf, L):
    x1, y1, z1 = sat_position_cbf
    x2, y2, z2 = gs_position_cbf
    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) **2)
    return dist <= L


def calculate_elevation_angle(sat_pos, observer_pos):   # degree 
    # Convert latitude and longitude from degrees to radians 
    sat_lat_rad, sat_lon_rad, _ = list(np.deg2rad(sat_pos))
    gs_lat_rad, gs_lon_rad, _ = list(np.deg2rad(observer_pos))

    # Calculate the difference in longitude
    d_lon = sat_lon_rad - gs_lon_rad

    # Calculate the distance between satellite and user in the horizontal plane
    distance_horizontal = np.arccos(
        np.sin(gs_lat_rad) * np.sin(sat_lat_rad) + np.cos(gs_lat_rad) * np.cos(sat_lat_rad) * np.cos(d_lon)
    ) * R

    # Calculate the elevation angle
    elevation_angle = np.arctan2(sat_pos[2] - observer_pos[2], distance_horizontal)

    # Convert elevation angle from radians to degrees
    elevation_angle_deg = np.degrees(elevation_angle)

    return elevation_angle_deg


# Function to calculate total link loss (L_i)
def calculate_link_loss(sat_pos, observer_pos):
    elevation_angle = calculate_elevation_angle(sat_pos, observer_pos)
    # print(elevation_angle)

    distance = math.sqrt(R**2 * (math.sin(math.radians(elevation_angle)))**2 + sat_pos[2]**2 + 2 * R * sat_pos[2]) - R * math.sin(math.radians(elevation_angle))
    p_los = 1 / (1 + a * math.exp(-180 * b * elevation_angle / math.pi + a * b))
    L_zenith = 90 - elevation_angle

    # Calculate the each link loss (L_a ~ L_d)
    L_a = L_zenith / math.sin(math.radians(elevation_angle))
    L_b = 20 * math.log10(c) + 20 * math.log10(distance) + 32.45
    L_sf = H_i * p_los + h_i * (1 - p_los)
    L_c = 1 / math.sqrt(2) * (27.5 * phi**1.26 * (f_c / 4)**(-1.5))
    L_d = 10 * math.log10(10**(0.1 * X) + 10**(0.1 * Y) + 10**(0.1 * Z))
    
    link_loss = L_a + L_b + L_sf + L_c + L_d
    return link_loss


def ipStr( ip ):
    """Generate IP address string from an unsigned int.
       ip: unsigned int of form w << 24 | x << 16 | y << 8 | z
       returns: ip address string w.x.y.z"""
    w = ( ip >> 24 ) & 0xff
    x = ( ip >> 16 ) & 0xff
    y = ( ip >> 8 ) & 0xff
    z = ip & 0xff
    return "%i.%i.%i.%i" % ( w, x, y, z )

def ipAdd( i, prefixLen=sub_mask, ipBaseNum=ipBaseNum ):
    """Return IP address string from ints
    i: int to be added to ipbase
    prefixLen: optional IP prefix length
    ipBaseNum: option base IP address as int
    returns IP address as string"""
    i=int(i)
    imax = 0xffffffff >> prefixLen
    assert i <= imax, 'Not enough IP addresses in the subnet'
    mask = 0xffffffff ^ imax
    ipnum = ( ipBaseNum & mask ) + i
    return ipStr( ipnum )


# Function to calculate average throughput and loss from CSV data
def calculate_averages(algorithm,log_index,link_bw):
    csv_file_path=f"{log_dir}/{log_index}/result/{algorithm}_{link_bw}.csv"
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        
        # Initialize variables to calculate sums
        total_throughput = 0
        total_loss = 0
        row_count = 0

        # Iterate through each row in the CSV file
        for row in csv_reader:
            total_throughput += float(row["Average Throughput (Mbps)"])
            total_loss += float(row["Packet Loss Rate (%)"])
            row_count += 1

        # Calculate averages
        average_throughput = total_throughput / row_count
        average_loss = total_loss / row_count

        return average_throughput, average_loss
    
def ipNum( w, x, y, z ):
    """Generate unsigned int from components of IP address
       returns: w << 24 | x << 16 | y << 8 | z"""
    return ( w << 24 ) | ( x << 16 ) | ( y << 8 ) | z

def ipParse( ip ):
    "Parse an IP address and return an unsigned int."
    args = [ int( arg ) for arg in ip.split( '.' ) ]

    return ipNum( *args )


def netParse( ipstr ):
    """Parse an IP network specification, returning
       address and prefix len as unsigned ints"""
    prefixLen = 0
    if '/' in ipstr:
        ip, pf = ipstr.split( '/' )
        prefixLen = int( pf )
    # if no prefix is specified, set the prefix to 24
    else:
        ip = ipstr
        prefixLen = 16
    return ipParse( ip ), prefixLen

def getHostID(hostIP):
    ipBaseNum, prefixLen = netParse( hostIP )
    hostID = ( 0xffffffff >> prefixLen ) & ipBaseNum
    return f"s{hostID}"


def get_unique_log_index():
    index = 0
    while os.path.exists(os.path.join(log_dir, str(index))):
        index += 1
    index =str(index)
    os.makedirs(os.path.join(log_dir, index), mode=0o777)
    os.makedirs(os.path.join(log_dir, index,"result"), mode=0o777)
    os.makedirs(os.path.join(log_dir, index,"client"), mode=0o777)
    os.makedirs(os.path.join(log_dir, index,"server"), mode=0o777)
    return index