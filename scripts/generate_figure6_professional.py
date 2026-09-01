import matplotlib.pyplot as plt
import numpy as np
import os

WORKSPACE_ROOT = r"d:\~Ideas n Innovation\~~Taiwan\AU\11_Task_Robotic\kuka_ros2"
IMAGES_DIR = os.path.join(WORKSPACE_ROOT, "images")

# Set global publication styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

def generate_figure6_professional_dashboard():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10.5, 7.2), dpi=300)
    
    models = ['Proposed\nROS 2 Stack', 'Octo Model\n(Ghosh 2024)', 'OpenVLA\n(Kim 2024)', 'RT-2 Policy\n(Brohan 2023)']
    colors = ['#27AE60', '#3498DB', '#E67E22', '#9B59B6']
    
    # -------------------------------------------------------------
    # (a) Cartesian Positioning Error (mm) - Lower is Better
    # -------------------------------------------------------------
    errors = [3.18, 14.20, 16.50, 18.00]
    b1 = ax1.bar(models, errors, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.0, zorder=3)
    ax1.set_ylabel('Cartesian Error (mm)', fontweight='bold', fontsize=9.5)
    ax1.set_title('(a) Positioning Precision (Lower is Better)', fontweight='bold', fontsize=10, pad=8)
    ax1.set_ylim(0, 22)
    ax1.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    # Suction cup threshold line
    ax1.axhline(8.0, color='#C0392B', linestyle='--', linewidth=1.5, zorder=4)
    ax1.text(1.5, 8.5, 'Vacuum Cup Seal Limit (8.0 mm)', color='#C0392B', fontsize=8, fontweight='bold', ha='center')
    
    for bar, val in zip(b1, errors):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4, f'{val:.2f} mm',
                 ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    
    # -------------------------------------------------------------
    # (b) Compute GPU VRAM Footprint (GB) - Lower is Better
    # -------------------------------------------------------------
    vram = [0.0, 8.0, 16.0, 48.0]
    b2 = ax2.bar(models, vram, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.0, zorder=3)
    ax2.set_ylabel('GPU Memory Required (GB)', fontweight='bold', fontsize=9.5)
    ax2.set_title('(b) GPU VRAM Requirement (Lower is Better)', fontweight='bold', fontsize=10, pad=8)
    ax2.set_ylim(0, 56)
    ax2.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(b2, vram):
        text = '0 MB (CPU)' if val == 0 else f'{int(val)} GB'
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.9, text,
                 ha='center', va='bottom', fontsize=8.5, fontweight='bold')
        
    # -------------------------------------------------------------
    # (c) End-to-End Decision Latency (seconds) - Lower is Better
    # -------------------------------------------------------------
    latency = [1.26, 18.50, 24.00, 32.00]
    b3 = ax3.bar(models, latency, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.0, zorder=3)
    ax3.set_ylabel('Decision Latency (s)', fontweight='bold', fontsize=9.5)
    ax3.set_title('(c) Task Decision & Planning Time (Lower is Better)', fontweight='bold', fontsize=10, pad=8)
    ax3.set_ylim(0, 38)
    ax3.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(b3, latency):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6, f'{val:.2f} s',
                 ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    # -------------------------------------------------------------
    # (d) Hardware Power Consumption (Watts) - Lower is Better
    # -------------------------------------------------------------
    power = [15.0, 220.0, 350.0, 500.0]
    b4 = ax4.bar(models, power, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.0, zorder=3)
    ax4.set_ylabel('Power Consumption (Watts)', fontweight='bold', fontsize=9.5)
    ax4.set_title('(d) Host Computational Power Draw (Lower is Better)', fontweight='bold', fontsize=10, pad=8)
    ax4.set_ylim(0, 580)
    ax4.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(b4, power):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 9, f'{int(val)} W',
                 ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.tight_layout(pad=2.2)
    out_path = os.path.join(IMAGES_DIR, "figure6_vla_benchmark_comparison.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Successfully generated professional Figure 6 at: {out_path}")

if __name__ == "__main__":
    generate_figure6_professional_dashboard()
