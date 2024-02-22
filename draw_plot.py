import csv
import matplotlib.pyplot as plt

# IEEE 저널 스타일 설정
# plt.style.use('seaborn-darkgrid')  # 'ieee' 스타일이 직접 지원되지 않으므로, 대체 스타일 사용

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
plt.savefig('throughput_comparison_graph.pdf')
plt.show()