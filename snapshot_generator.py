# new_sat_tle_map = dict();
# old_sat_tle_map = dict();

# new_snapshot_filename = "satcp/report_timing_error/raw/starlink_new.txt";
# old_snapshot_filename = "satcp/report_timing_error/raw/starlink_old.txt";

# new_snapshot_file = open(new_snapshot_filename, "r")
# old_snapshot_file = open(old_snapshot_filename, "r")
# current_sat = None

# for line in new_snapshot_file:
#     # if this is the satellite name line
#     if len(line.split()) == 1 and "STARLINK" in line:
#         current_sat = (line.split())[0]
#         new_sat_tle_map[current_sat] = []
#     # else this is the data line for the current satellite
#     else:
#         new_sat_tle_map[current_sat].append(line)
# print(len(new_sat_tle_map))

# for line in old_snapshot_file:
#     # if this is the satellite name line
#     if len(line.split()) == 1 and "STARLINK" in line:
#         current_sat = (line.split())[0]
#         old_sat_tle_map[current_sat] = []
#     # else this is the data line for the current satellite
#     else:
#         old_sat_tle_map[current_sat].append(line)
# print(len(old_sat_tle_map))

# for sat in new_sat_tle_map:
#     if sat not in old_sat_tle_map:
#         continue
#     sat_new_tle = new_sat_tle_map[sat]
#     sat_old_tle = old_sat_tle_map[sat]
#     if sat_new_tle == sat_old_tle:
#         continue
#     sat_new_tle[0] = sat_new_tle[0][:2] + "1" + sat_new_tle[0][3:]
#     sat_new_tle[1] = sat_new_tle[1][:2] + "1" + sat_new_tle[1][3:]

#     f_new = open("tle/new/%s.tle" % sat, "w")
#     f_new.write(sat)
#     f_new.write("\n")
#     f_new.write(sat_new_tle[0])
#     f_new.write(sat_new_tle[1])
#     f_new.close()

#     sat_old_tle[0] = sat_old_tle[0][:2] + "2" + sat_old_tle[0][3:]
#     sat_old_tle[1] = sat_old_tle[1][:2] + "2" + sat_old_tle[1][3:]

#     f_old = open("tle/old/%s.tle" % sat, "w")
#     f_old.write(sat)
#     f_old.write("\n")
#     f_old.write(sat_old_tle[0])
#     f_old.write(sat_old_tle[1])
#     f_old.close()

# new_snapshot_file.close()
# old_snapshot_file.close()

from datetime import datetime
import numpy as np
from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv
from astropy import units as u
from astropy.time import Time, TimeDelta
from astropy.coordinates import EarthLocation, GCRS, ITRS
from astropy.coordinates import CartesianRepresentation
from scipy.io import savemat

# Function to load TLE data and create satellite objects
def load_tle_data(file_path):
    tle_data = []
    with open(file_path, 'r') as tle_file:
        lines = tle_file.readlines()
        for i in range(0, len(lines), 3):
            sat_name = lines[i].strip()
            tle_line1 = lines[i + 1].strip()
            tle_line2 = lines[i + 2].strip()
            satellite = twoline2rv(tle_line1, tle_line2, wgs84)
            tle_data.append((sat_name, satellite))
    return tle_data

# Function to calculate satellite positions and save them to a .mat file
def calculate_and_save_satellite_positions(tle_data, num_periods, time_step, output_file):
    positions = {}
    sat_id = 1
    for sat_name, satellite in tle_data:
        if sat_id % 100 == 1:
            print(f"------------ Satellite {sat_id} / {len(tle_data)} ------------")
        lla_positions = []
        for period in range(num_periods):
            current_time = Time(datetime.utcnow()) + TimeDelta(period * time_step)
            current_datetime = current_time.utc.datetime
            position_velocity, _ = satellite.propagate(current_datetime.year, current_datetime.month, current_datetime.day, current_datetime.hour, current_datetime.minute, current_datetime.second + current_datetime.microsecond / 1e6)
            position = np.array(position_velocity[:3]) * u.km
            gcrs = GCRS(CartesianRepresentation(position), obstime=current_time)
            itrs = gcrs.transform_to(ITRS(obstime=current_time))
            earth_location = EarthLocation.from_geocentric(*itrs.cartesian.xyz)
            lla = earth_location.to_geodetic()
            lla_positions.append([lla.lat.value, lla.lon.value, lla.height.value])
        positions[sat_name] = lla_positions
        sat_id += 1
    # Save to .mat file
    savemat(output_file, positions)

if __name__ == "__main__":
    tle_file_path = 'Starlink.tle'
    num_periods = 30  # Number of time periods to calculate
    time_step = 1.0 * u.minute  # Time interval
    output_mat_file = 'starlink_positions.mat'  # Output .mat file name

    tle_data = load_tle_data(tle_file_path)
    calculate_and_save_satellite_positions(tle_data, num_periods, time_step, output_mat_file)

    print(f"Satellite positions saved to '{output_mat_file}'.")
