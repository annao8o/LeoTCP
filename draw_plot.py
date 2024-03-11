import csv
import matplotlib.pyplot as plt
import numpy as np
from config import results_file

# IEEE 저널 스타일 설정
# plt.style.use('seaborn-darkgrid')  # 'ieee' 스타일이 직접 지원되지 않으므로, 대체 스타일 사용
'''
throughput_values1 = []
throughput_values2 = []
throughput_values3 = []

# 첫 번째 CSV 파일에서 throughput 값 읽기
with open('log/server/results_proposed.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # 헤더 스킵
    for row in csvreader:
        throughput = float(row[2])  # Throughput 값이 세 번째 열에 있음
        throughput_values1.append(throughput)

# 두 번째 CSV 파일에서 throughput 값 읽기
with open('log/server/results_satcp_0.4.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # 헤더 스킵
    for row in csvreader:
        throughput = float(row[2]) 
        throughput_values2.append(throughput)

# 두 번째 CSV 파일에서 throughput 값 읽기
with open('log/server/results_satcp.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # 헤더 스킵
    for row in csvreader:
        throughput = float(row[2])  
        throughput_values3.append(throughput)

# x 축을 위한 인덱스 생성
x = list(range(1, max(len(throughput_values1), len(throughput_values2), len(throughput_values3)) + 1))

# 그래프 생성
plt.figure(figsize=(10, 6))
plt.plot(x[:len(throughput_values1)], throughput_values1, marker='o', linestyle='-', color='b', label='Proposed')
plt.plot(x[:len(throughput_values2)], throughput_values2, marker='v', linestyle='--', color='g', label='Satcp-0.4')
plt.plot(x[:len(throughput_values3)], throughput_values3, marker='s', linestyle='--', color='r', label='Satcp-0.6')

# 그래프 제목과 축 라벨 설정
plt.title('Throughput Comparison')
plt.xlabel('Time Step')
plt.ylabel('Throughput (Mbps)')

# 범례 추가
plt.legend()

# 그리드 추가
plt.grid(True)

# 그래프 저장 및 보여주기
plt.savefig('save/throughput_comparison_graph.pdf')
plt.show()
'''
# Define a dictionary to hold your data
data = {}

# Read your data from the CSV file
with open(results_file, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        algorithm = row['Algorithm Name']
        bandwidth = float(row['Bandwidth (Mbps)'])
        throughput = float(row['Average Throughput(Mbps)'])
        
        if algorithm == "satcp_0.3":
            continue

        if algorithm not in data:
            data[algorithm] = {'bandwidth': [], 'throughput': []}
        
        data[algorithm]['bandwidth'].append(bandwidth)
        data[algorithm]['throughput'].append(throughput)

# Get the min and max bandwidth to set x-axis limits
min_bandwidth = min(min(d['bandwidth']) for d in data.values())
max_bandwidth = max(max(d['bandwidth']) for d in data.values())
bandwidth_ticks = sorted({b for alg_data in data.values() for b in alg_data['bandwidth']})

# Set a buffer for xlim to prevent the lines from touching the plot walls
xlim_buffer = (max_bandwidth - min_bandwidth) * 0.05  # 5% buffer on each side

# Create the plot
plt.figure(figsize=(8, 6))

for algorithm, values in data.items():
    # Sort the data by bandwidth for plotting
    sorted_data = sorted(zip(values['bandwidth'], values['throughput']))
    bandwidths, throughputs = zip(*sorted_data)
    
    plt.plot(bandwidths, throughputs, marker='o', label=algorithm)

# Set x-axis range with a buffer and y-axis range to data extremes
plt.xlim(min_bandwidth - xlim_buffer, max_bandwidth + xlim_buffer)

# Set the x-ticks to show up in between the data points
plt.xticks(bandwidth_ticks)

plt.xlabel('Bandwidth (Mbps)', fontsize=12)
plt.ylabel('Average Throughput (Mbps)', fontsize=12)
plt.legend(fontsize=10)
plt.grid(True)

plt.tight_layout()

# Save the figure
plt.savefig('save/throughput_comparison_graph.pdf')
plt.show()