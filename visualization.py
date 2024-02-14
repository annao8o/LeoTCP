import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.io import loadmat
from mpl_toolkits.mplot3d import Axes3D

# Load data from .mat file
data = loadmat('starlink_positions.mat')

# Select a single satellite
key = 'STARLINK-1007'
positions = data[key]
R = 6371000  # Radius of the Earth in meters

def lla_to_xyz(lat, lon, alt):
    x = (R + alt) * np.cos(lat) * np.cos(lon)
    y = (R + alt) * np.cos(lat) * np.sin(lon)
    z = (R + alt) * np.sin(lat)
    return x, y, z

# Convert data
xyz_positions = np.array([lla_to_xyz(np.radians(lat), np.radians(lon), alt) for lat, lon, alt in positions])

# Determine plot limits based on actual data range
# Here we use a larger range to ensure we can see the satellite orbiting around the Earth
max_range = np.max(np.abs(xyz_positions)) * 1.5  # Use a larger range

# Create a figure with larger size
fig = plt.figure(figsize=(10, 10))  # Increase the figure size
ax = fig.add_subplot(111, projection='3d')


# Set the plot limits
ax.set_xlim(-max_range, max_range)
ax.set_ylim(-max_range, max_range)
ax.set_zlim(-max_range, max_range)

# Adjust the viewing angle
ax.view_init(elev=30, azim=120)

def update(frame):
    ax.clear()
    # Redraw Earth

    x, y, z = xyz_positions[frame, :]
    ax.scatter(x, y, z, marker='o', s=50, color='r')
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)

    return ax,

num_frames = xyz_positions.shape[0]
ani = FuncAnimation(fig, update, frames=np.arange(0, num_frames), interval=50)

plt.show()
ani.save('satellite_ani.gif', writer='imagemagick')
