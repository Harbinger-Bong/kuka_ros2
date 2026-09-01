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
plt.rcParams['axes.linewidth'] = 1.2

def generate_figure4a_standalone():
    """Generates Figure 4(a) standalone with large, bold fonts."""
    fig, ax = plt.subplots(figsize=(8.0, 5.2), dpi=300)
    
    stages = [
        'Acoustic ASR\n(Offline Engine)',
        'Motion Planning\n(MoveIt 2 Pilz)',
        'Vision Mapping\n(12-ArUco SVD)',
        'Socket Bridge\n(Network Stream)',
        'Intent Parsing\n(Phonetic Map)'
    ]
    latencies = [685, 475, 52, 36, 14]
    errors = [52, 40, 8, 9, 3]
    colors = ['#1F4E79', '#2E75B6', '#00B050', '#7030A0', '#ED7D31']
    
    y_pos = np.arange(len(stages))
    bars = ax.barh(y_pos, latencies[::-1], xerr=errors[::-1], color=colors[::-1],
                   capsize=6, edgecolor='#1B2631', linewidth=1.4, height=0.62, zorder=3)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages[::-1], fontsize=13, fontweight='bold', color='#1A252C')
    ax.set_xlabel('Execution Latency (milliseconds)', fontsize=14, fontweight='bold', color='#1A252C', labelpad=10)
    ax.set_title('Subsystem Latency Breakdown (Mean ± Std Dev)', fontsize=15, fontweight='bold', color='#0F2537', pad=15)
    ax.set_xlim(0, 880)
    ax.grid(axis='x', linestyle='--', alpha=0.5, zorder=1)
    
    # Annotate bars with large text
    for bar, lat, err in zip(bars, latencies[::-1], errors[::-1]):
        w = bar.get_width()
        pct = (lat / 1262.0) * 100.0
        ax.text(w + err + 18, bar.get_y() + bar.get_height()/2, f'{lat} ms ({pct:.1f}%)',
                va='center', ha='left', fontsize=12, fontweight='bold', color='#1A252C')
        
    plt.tight_layout()
    out_paths = [
        os.path.join(IMAGES_DIR, "figure4a_subsystem_latency.png"),
        os.path.join(OVERLEAF_IMAGES, "figure4a_subsystem_latency.png"),
        os.path.join(CONF_IMAGES, "figure4a_subsystem_latency.png"),
        os.path.join(REVISE_IMAGES, "figure4a_subsystem_latency.png")
    ]
    for p in out_paths:
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Figure 4a (Standalone): {out_paths[0]}")

def generate_figure4b_standalone():
    """Generates Figure 4(b) standalone with large, bold fonts."""
    fig, ax = plt.subplots(figsize=(6.5, 5.2), dpi=300)
    
    total_time = 1.262
    hri_target = 1.500
    
    categories = ['Proposed Framework\n(Decision Latency)', 'HRI Acceptable\nThreshold Limit']
    times = [total_time, hri_target]
    bar_colors = ['#27AE60', '#C0392B']
    
    bars = ax.bar(categories, times, color=bar_colors, width=0.48, edgecolor='#1B2631', linewidth=1.4, zorder=3)
    ax.set_ylabel('Total Decision Time (seconds)', fontsize=14, fontweight='bold', color='#1A252C', labelpad=10)
    ax.set_title('Total Response Latency vs. HRI Target', fontsize=15, fontweight='bold', color='#0F2537', pad=15)
    ax.set_ylim(0, 2.05)
    ax.set_xticklabels(categories, fontsize=12.5, fontweight='bold', color='#1A252C')
    ax.tick_params(axis='y', labelsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=1)
    
    # HRI target reference dashed line
    ax.axhline(hri_target, color='#922B21', linestyle='--', linewidth=2.0, alpha=0.85, zorder=2)
    ax.text(0.5, hri_target + 0.06, 'Max Safe HRI Latency (1.50 s)', color='#922B21',
            ha='center', fontsize=12, fontweight='bold', zorder=4)
    
    # Annotate bars
    for bar, t in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{t:.2f} s',
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='#1A252C')
        
    plt.tight_layout()
    out_paths = [
        os.path.join(IMAGES_DIR, "figure4b_total_decision_latency.png"),
        os.path.join(OVERLEAF_IMAGES, "figure4b_total_decision_latency.png"),
        os.path.join(CONF_IMAGES, "figure4b_total_decision_latency.png"),
        os.path.join(REVISE_IMAGES, "figure4b_total_decision_latency.png")
    ]
    for p in out_paths:
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Figure 4b (Standalone): {out_paths[0]}")

def generate_figure4_combined_large_font():
    """Generates Figure 4 (Combined) with extra large, clear fonts."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.0, 5.0), dpi=300, gridspec_kw={'width_ratios': [1.35, 1.0]})
    
    # Subplot 1: Subsystem Breakdown Bar Chart
    stages = [
        'Acoustic ASR\n(Offline Engine)',
        'Motion Planning\n(MoveIt 2 Pilz)',
        'Vision Mapping\n(12-ArUco SVD)',
        'Socket Bridge\n(Network Stream)',
        'Intent Parsing\n(Phonetic Map)'
    ]
    latencies = [685, 475, 52, 36, 14]
    errors = [52, 40, 8, 9, 3]
    colors = ['#1F4E79', '#2E75B6', '#00B050', '#7030A0', '#ED7D31']
    
    y_pos = np.arange(len(stages))
    bars1 = ax1.barh(y_pos, latencies[::-1], xerr=errors[::-1], color=colors[::-1],
                    capsize=5, edgecolor='#1B2631', linewidth=1.2, height=0.60, zorder=3)
    
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(stages[::-1], fontsize=11.5, fontweight='bold', color='#1A252C')
    ax1.set_xlabel('Execution Latency (ms)', fontsize=12.5, fontweight='bold', color='#1A252C', labelpad=8)
    ax1.set_title('(a) Subsystem Latency Breakdown (Mean ± Std)', fontsize=13.5, fontweight='bold', color='#0F2537', pad=12)
    ax1.set_xlim(0, 890)
    ax1.tick_params(axis='x', labelsize=11)
    ax1.grid(axis='x', linestyle='--', alpha=0.5, zorder=1)
    
    for bar, lat, err in zip(bars1, latencies[::-1], errors[::-1]):
        w = bar.get_width()
        pct = (lat / 1262.0) * 100.0
        ax1.text(w + err + 16, bar.get_y() + bar.get_height()/2, f'{lat} ms ({pct:.1f}%)',
                 va='center', ha='left', fontsize=10.5, fontweight='bold', color='#1A252C')
    
    # Subplot 2: Total Decision Latency vs HRI Target
    total_time = 1.262
    hri_target = 1.500
    
    categories = ['Proposed Stack\n(Decision Latency)', 'HRI Safe Target\nThreshold Limit']
    times = [total_time, hri_target]
    bar_colors = ['#27AE60', '#C0392B']
    
    bars2 = ax2.bar(categories, times, color=bar_colors, width=0.46, edgecolor='#1B2631', linewidth=1.2, zorder=3)
    ax2.set_ylabel('Total Decision Time (seconds)', fontsize=12.5, fontweight='bold', color='#1A252C', labelpad=8)
    ax2.set_title('(b) Total Response vs. HRI Target', fontsize=13.5, fontweight='bold', color='#0F2537', pad=12)
    ax2.set_ylim(0, 2.05)
    ax2.set_xticklabels(categories, fontsize=11.5, fontweight='bold', color='#1A252C')
    ax2.tick_params(axis='y', labelsize=11)
    ax2.grid(axis='y', linestyle='--', alpha=0.5, zorder=1)
    
    ax2.axhline(hri_target, color='#922B21', linestyle='--', linewidth=1.8, alpha=0.85, zorder=2)
    ax2.text(0.5, hri_target + 0.05, 'Max Safe HRI Latency (1.50 s)', color='#922B21',
            ha='center', fontsize=10.5, fontweight='bold', zorder=4)
    
    for bar, t in zip(bars2, times):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{t:.2f} s',
                 ha='center', va='bottom', fontsize=12.0, fontweight='bold', color='#1A252C')
    
    plt.tight_layout()
    out_paths = [
        os.path.join(IMAGES_DIR, "figure4_latency_chart.png"),
        os.path.join(OVERLEAF_IMAGES, "figure4_latency_chart.png"),
        os.path.join(MAMM_IMAGES, "figure4_latency_chart.png"),
        os.path.join(CONF_IMAGES, "figure4_latency_chart.png"),
        os.path.join(REVISE_IMAGES, "figure4_latency_chart.png")
    ]
    for p in out_paths:
        plt.savefig(p, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated Figure 4 (Combined Enlarged): {out_paths[0]}")

if __name__ == "__main__":
    generate_figure4a_standalone()
    generate_figure4b_standalone()
    generate_figure4_combined_large_font()
    print("All Figure 4 variations generated successfully!")
