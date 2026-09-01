import matplotlib.pyplot as plt
import numpy as np
import os
import shutil

WORKSPACE_ROOT = r"d:\~Ideas n Innovation\~~Taiwan\AU\11_Task_Robotic\kuka_ros2"
IMAGES_DIR = os.path.join(WORKSPACE_ROOT, "images")
OVERLEAF_IMAGES = os.path.join(WORKSPACE_ROOT, "Journal", "Overleaf_Submission_Package", "images")
MAMM_IMAGES = os.path.join(WORKSPACE_ROOT, "Journal", "MAMM'", "Latex", "images")
CONF_IMAGES = r"D:\Download Move1\Jurnal_lolo\From Gilang\conf\images"
REVISE_IMAGES = r"D:\Download Move1\Jurnal_lolo\From Gilang\Revise\images"

for d in [IMAGES_DIR, OVERLEAF_IMAGES, MAMM_IMAGES, CONF_IMAGES, REVISE_IMAGES]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------
# Global Typography & Style for High Readability
# -------------------------------------------------------------
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.weight'] = 'bold'
plt.rcParams['axes.edgecolor'] = '#2C3E50'
plt.rcParams['axes.linewidth'] = 1.3

def generate_figure6_enlarged_dashboard():
    """Generates Figure 6 with extra large, bold typography across all 4 subplots."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12.5, 8.8), dpi=300)
    
    models = ['Proposed\nFramework', 'Octo Model\n(Ghosh 2024)', 'OpenVLA\n(Kim 2024)', 'RT-2 Policy\n(Brohan 2023)']
    colors = ['#1E8449', '#2E86C1', '#D35400', '#7D3C98']
    x_pos = np.arange(len(models))
    
    # -------------------------------------------------------------
    # (a) Cartesian Positioning Error (mm) - Lower is Better
    # -------------------------------------------------------------
    errors = [3.18, 14.20, 16.50, 18.00]
    b1 = ax1.bar(x_pos, errors, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.3, zorder=3)
    ax1.set_ylabel('Cartesian Error (mm)', fontsize=12.5, fontweight='bold', color='#1A252C', labelpad=8)
    ax1.set_title('(a) Positioning Precision (Lower is Better)', fontsize=13.5, fontweight='bold', color='#0F2537', pad=10)
    ax1.set_ylim(0, 23)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(models, fontsize=11.5, fontweight='bold', color='#1A252C')
    ax1.tick_params(axis='y', labelsize=11.5)
    ax1.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    # Suction cup threshold line
    ax1.axhline(8.0, color='#C0392B', linestyle='--', linewidth=2.0, zorder=4)
    ax1.text(1.5, 8.6, 'Suction Cup Sealing Limit (8.0 mm)', color='#C0392B', fontsize=11.0, fontweight='bold', ha='center', zorder=5)
    
    for bar, val in zip(b1, errors):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.45, f'{val:.2f} mm',
                 ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='#1A252C')
    
    # -------------------------------------------------------------
    # (b) Compute GPU VRAM Footprint (GB) - Lower is Better
    # -------------------------------------------------------------
    vram = [0.0, 8.0, 16.0, 48.0]
    b2 = ax2.bar(x_pos, vram, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.3, zorder=3)
    ax2.set_ylabel('GPU Memory Required (GB)', fontsize=12.5, fontweight='bold', color='#1A252C', labelpad=8)
    ax2.set_title('(b) GPU VRAM Requirement (Lower is Better)', fontsize=13.5, fontweight='bold', color='#0F2537', pad=10)
    ax2.set_ylim(0, 58)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(models, fontsize=11.5, fontweight='bold', color='#1A252C')
    ax2.tick_params(axis='y', labelsize=11.5)
    ax2.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(b2, vram):
        text = '0 MB (CPU)' if val == 0 else f'{int(val)} GB'
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.1, text,
                 ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='#1A252C')
        
    # -------------------------------------------------------------
    # (c) End-to-End Decision Latency (seconds) - Lower is Better
    # -------------------------------------------------------------
    latency = [1.26, 18.50, 24.00, 32.00]
    b3 = ax3.bar(x_pos, latency, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.3, zorder=3)
    ax3.set_ylabel('Decision Latency (seconds)', fontsize=12.5, fontweight='bold', color='#1A252C', labelpad=8)
    ax3.set_title('(c) Task Decision & Planning Time (Lower is Better)', fontsize=13.5, fontweight='bold', color='#0F2537', pad=10)
    ax3.set_ylim(0, 39)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(models, fontsize=11.5, fontweight='bold', color='#1A252C')
    ax3.tick_params(axis='y', labelsize=11.5)
    ax3.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(b3, latency):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.7, f'{val:.2f} s',
                 ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='#1A252C')

    # -------------------------------------------------------------
    # (d) Hardware Power Consumption (Watts) - Lower is Better
    # -------------------------------------------------------------
    power = [15.0, 220.0, 350.0, 500.0]
    b4 = ax4.bar(x_pos, power, color=colors, width=0.52, edgecolor='#1B2631', linewidth=1.3, zorder=3)
    ax4.set_ylabel('Power Consumption (Watts)', fontsize=12.5, fontweight='bold', color='#1A252C', labelpad=8)
    ax4.set_title('(d) Host Computational Power Draw (Lower is Better)', fontsize=13.5, fontweight='bold', color='#0F2537', pad=10)
    ax4.set_ylim(0, 600)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(models, fontsize=11.5, fontweight='bold', color='#1A252C')
    ax4.tick_params(axis='y', labelsize=11.5)
    ax4.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(b4, power):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 11, f'{int(val)} W',
                 ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='#1A252C')

    plt.tight_layout(pad=2.5)
    
    out_paths = [
        os.path.join(IMAGES_DIR, "figure6_vla_benchmark_comparison.png"),
        os.path.join(OVERLEAF_IMAGES, "figure6_vla_benchmark_comparison.png"),
        os.path.join(MAMM_IMAGES, "figure6_vla_benchmark_comparison.png"),
        os.path.join(CONF_IMAGES, "figure6_vla_benchmark_comparison.png"),
        os.path.join(REVISE_IMAGES, "figure6_vla_benchmark_comparison.png")
    ]
    for p in out_paths:
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Figure 6 (Enlarged): {out_paths[0]}")

if __name__ == "__main__":
    generate_figure6_enlarged_dashboard()
