import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/performance_results.csv")

averages = df.groupby("clients")["throughput_mib_s"].mean()

print("\nAverage throughput:")
print(averages.round(2))

plt.figure(figsize=(9, 5))
plt.plot(averages.index, averages.values, marker="o")

plt.title("Concurrent File Sharing Performance")
plt.xlabel("Number of Concurrent Clients")
plt.ylabel("Average Throughput (MiB/s)")
plt.xticks([1, 2, 3])
plt.grid(True)

plt.tight_layout()
plt.savefig("results/concurrent_throughput.png", dpi=300)

print("\nGraph saved: results/concurrent_throughput.png")
