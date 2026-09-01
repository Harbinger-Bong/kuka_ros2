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

def generate_figure5_enlarged():
    """Generates Figure 5 with extra large, crisp typography."""
    fig, ax = plt.subplots(figsize=(9.2, 5.4), dpi=300)
    
    runs = ['Run 1\n(Red)', 'Run 2\n(Yellow)', 'Run 3\n(Blue)', 'Run 4\n(Red)', 'Run 5\n(Yellow)', 'Overall\nMean']
    errors = [3.20, 2.90, 3.40, 2.80, 3.60, 3.18]
    bar_colors = ['#1F4E79', '#1F4E79', '#1F4E79', '#1F4E79', '#1F4E79', '#0E6655']
    
    x_pos = np.arange(len(runs))
    bars = ax.bar(x_pos, errors, color=bar_colors, width=0.52, edgecolor='#1B2631', linewidth=1.4, zorder=3)
    
    # Error bar on overall mean (Mean ± Std: 3.18 ± 0.33 mm)
    ax.errorbar(5, 3.18, yerr=0.33, fmt='none', ecolor='#111111', capsize=6, capthick=2.0, elinewidth=2.0, zorder=4)
    
    # Threshold Constants
    r_cup = 8.0
    vla_err = 15.0
    
    # Threshold Lines with Large Labels
    ax.axhline(r_cup, color='#27AE60', linestyle='--', linewidth=2.2, label=r'Suction Sealing Tolerance Limit ($r_{\mathrm{cup}} = 8.0$ mm)', zorder=2)
    ax.axhline(vla_err, color='#C0392B', linestyle='-.', linewidth=2.2, label=r'Typical VLA Model Error Baseline ($\sim 15.0$ mm)', zorder=2)
    
    # Shaded Safe Region
    ax.axhspan(0, r_cup, facecolor='#E8F8F5', alpha=0.55, label='Airtight Vacuum Sealing Safe Operating Zone', zorder=1)
    
    # Axis formatting with large fonts
    ax.set_ylabel('Cartesian Positioning Error (mm)', fontsize=13.5, fontweight='bold', color='#1A252C', labelpad=10)
    ax.set_title('Physical Cartesian Precision vs. Sealing Limit and VLA Baseline', fontsize=14.5, fontweight='bold', color='#0F2537', pad=15)
    ax.set_ylim(0, 18.5)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(runs, fontsize=12.0, fontweight='bold', color='#1A252C')
    ax.tick_params(axis='y', labelsize=12)
    ax.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    # Value annotations on bars
    for bar, val in zip(bars, errors):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.38, f'{val:.2f} mm',
                ha='center', va='bottom', fontsize=11.5, fontweight='bold', color='#1A252C')
        
    # Legend with large bold font
    ax.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#BDC3C7', framealpha=0.95, fontsize=10.5)
    
    plt.tight_layout()
    out_paths = [
        os.path.join(IMAGES_DIR, "figure5_position_error_chart.png"),
        os.path.join(OVERLEAF_IMAGES, "figure5_position_error_chart.png"),
        os.path.join(MAMM_IMAGES, "figure5_position_error_chart.png"),
        os.path.join(CONF_IMAGES, "figure5_position_error_chart.png"),
        os.path.join(REVISE_IMAGES, "figure5_position_error_chart.png")
    ]
    for p in out_paths:
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Figure 5 (Enlarged): {out_paths[0]}")

if __name__ == "__main__":
    generate_figure5_enlarged()
