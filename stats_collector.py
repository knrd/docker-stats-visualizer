import subprocess
import sys
from datetime import datetime

def collect_docker_stats():
    """Collect the continuous stream of docker stats and save it with timestamps"""
    filename = f'docker_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # Use docker stats with custom format, including timestamp
    cmd = ['docker', 'stats', '--format', 'name={{.Name}}\tcpu={{.CPUPerc}}\tmem={{.MemUsage}}\tnet={{.NetIO}}\tblock={{.BlockIO}}']
    
    try:
        # Open the file for writing
        with open(filename, 'w') as f:
            # Run docker stats and capture its output
            print(" ".join(cmd))
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            
            print(f"Collecting stats to {filename}")
            print("Press Ctrl+C to stop...")
            
            # Read and write each line as it comes
            for line in process.stdout:
                timestamp = datetime.now().isoformat()
                f.write(f"{timestamp}\t{line}")
                f.flush()  # Ensure data is written immediately
                
    except KeyboardInterrupt:
        print("\nStopping stats collection...")
        process.terminate()
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error: {e}")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    collect_docker_stats()

