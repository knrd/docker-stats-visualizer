import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

def parse_size(size_str):
    """Convert Docker size strings (like 123MiB, 1.5GiB) to MB"""
    if not size_str or size_str == '0B':
        return 0
    
    match = re.match(r'([\d.]+)([A-Za-z]+)', size_str.strip())
    if not match:
        return 0
        
    value, unit = float(match.group(1)), match.group(2).lower()
    
    multipliers = {
        'b': 1/(1024*1024),
        'kb': 1/1024,
        'mb': 1,
        'gb': 1024,
        'tb': 1024*1024,
        'kib': 1/1024,
        'mib': 1,
        'gib': 1024,
        'tib': 1024*1024
    }
    
    return value * multipliers.get(unit, 0)

def clean_line(line):
    """Clean control characters and unnecessary parts from the line"""
    # Remove control sequences
    line = re.sub(r'\[([0-9;]*[A-Za-z]|\[K)', '', line)
    # Remove [H, [J, [K at the start or end of lines
    line = re.sub(r'(\[H|\[J|\[K)', '', line)
    return line.strip()

def parse_docker_stats(filename):
    """Parse the Docker stats log file into a DataFrame"""
    data = []
    with open(filename, 'r') as f:
        for line in f:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Clean the line
            line = clean_line(line)
            
            # Split by tabs
            parts = line.split('\t')
            
            # Skip if not enough parts
            if len(parts) < 5:
                continue
            
            try:
                entry = {
                    'timestamp': pd.to_datetime(parts[0]),
                    'name': parts[1].replace('name=', ''),
                    'cpu': float(parts[2].replace('cpu=', '').replace('%', '')),
                    'mem': parts[3].replace('mem=', '')
                }
                
                # Parse memory
                mem_parts = entry['mem'].split('/')
                entry['mem_used'] = parse_size(mem_parts[0].strip())
                entry['mem_total'] = parse_size(mem_parts[1].strip())
                
                # Parse network I/O
                net = parts[4].replace('net=', '')
                net_parts = net.split('/')
                entry['net_in'] = parse_size(net_parts[0].strip())
                entry['net_out'] = parse_size(net_parts[1].strip())
                
                # Parse block I/O
                if len(parts) > 5:
                    block = parts[5].replace('block=', '')
                    block_parts = block.split('/')
                    entry['block_in'] = parse_size(block_parts[0].strip())
                    entry['block_out'] = parse_size(block_parts[1].strip())
                else:
                    entry['block_in'] = 0
                    entry['block_out'] = 0
                
                data.append(entry)
            except (ValueError, IndexError) as e:
                continue
    
    return pd.DataFrame(data)

def create_visualization(df):
    """Create an interactive HTML visualization of the Docker stats"""
    # Get unique container names
    containers = df['name'].unique()
    
    # Create subplot figure
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=('CPU Usage (%)', 'Memory Usage (MB)', 'Network I/O (MB)', 'Block I/O (MB)'),
        shared_xaxes=True,
        vertical_spacing=0.1
    )
    
    # Color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, container in enumerate(containers):
        container_data = df[df['name'] == container]
        color = colors[i % len(colors)]
        
        # CPU plot
        fig.add_trace(
            go.Scatter(x=container_data['timestamp'], y=container_data['cpu'],
                      name=f"{container} - CPU",
                      line=dict(color=color)),
            row=1, col=1
        )
        
        # Memory plot
        fig.add_trace(
            go.Scatter(x=container_data['timestamp'], y=container_data['mem_used'],
                      name=f"{container} - Memory",
                      line=dict(color=color)),
            row=2, col=1
        )
        
        # Network I/O plot
        fig.add_trace(
            go.Scatter(x=container_data['timestamp'], y=container_data['net_in'],
                      name=f"{container} - Net In",
                      line=dict(color=color, dash='solid')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=container_data['timestamp'], y=container_data['net_out'],
                      name=f"{container} - Net Out",
                      line=dict(color=color, dash='dash')),
            row=3, col=1
        )
        
        # Block I/O plot
        fig.add_trace(
            go.Scatter(x=container_data['timestamp'], y=container_data['block_in'],
                      name=f"{container} - Block In",
                      line=dict(color=color, dash='solid')),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=container_data['timestamp'], y=container_data['block_out'],
                      name=f"{container} - Block Out",
                      line=dict(color=color, dash='dash')),
            row=4, col=1
        )
    
    # After creating subplots, update the layout to set height
    fig.update_layout(
        height=1200,
        title='Docker Container Performance Metrics',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        ),
        margin=dict(r=200)
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="CPU %", row=1, col=1)
    fig.update_yaxes(title_text="Memory (MB)", row=2, col=1)
    fig.update_yaxes(title_text="Network I/O (MB)", row=3, col=1)
    fig.update_yaxes(title_text="Block I/O (MB)", row=4, col=1)
    
    return fig

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python visualize_stats.py <stats_log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    output_file = log_file.rsplit('.', 1)[0] + '_visualization.html'
    
    print(f"Parsing {log_file}...")
    df = parse_docker_stats(log_file)
    
    print("Creating visualization...")
    fig = create_visualization(df)
    
    print(f"Saving visualization to {output_file}...")
    fig.write_html(output_file)
    print("Done!")

if __name__ == "__main__":
    main()
