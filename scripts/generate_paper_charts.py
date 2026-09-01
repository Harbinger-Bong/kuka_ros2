import matplotlib.pyplot as plt
import numpy as np
import os

WORKSPACE_ROOT = r"d:\~Ideas n Innovation\~~Taiwan\AU\11_Task_Robotic\kuka_ros2"
IMAGES_DIR = os.path.join(WORKSPACE_ROOT, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Set global publication styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

def generate_figure4_latency_chart():
    """Generates a high-res latency breakdown chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), dpi=300, gridspec_kw={'width_ratios': [1.3, 1.0]})
    
    # Subplot 1: Subsystem Breakdown Bar Chart
    stages = ['Acoustic ASR\n(Vosk 16kHz)', 'Motion Planning\n(MoveIt 2 Pilz)', 'Vision Mapping\n(12-ArUco SVD)', 'EKI Socket\n(XML Telemetry)', 'Intent Parsing\n(Phonetic Map)']
    latencies = [685, 475, 52, 36, 14]
    errors = [52, 40, 8, 9, 3]
    colors = ['#2B5C8F', '#3498DB', '#1ABC9C', '#9B59B6', '#E67E22']
    
    bars = ax1.barh(stages[::-1], latencies[::-1], xerr=errors[::-1], color=colors[::-1], capsize=4, edgecolor='#2C3E50', height=0.6)
    ax1.set_xlabel('Execution Latency (ms)', fontweight='bold', fontsize=10)
    ax1.set_title('(a) Subsystem Latency Breakdown (Mean ± Std)', fontweight='bold', fontsize=10.5, pad=10)
    ax1.grid(axis='x', linestyle='--', alpha=0.5)
    ax1.set_xlim(0, 800)
    
    for bar, lat, err in zip(bars, latencies[::-1], errors[::-1]):
        w = bar.get_width()
        ax1.text(w + err + 18, bar.get_y() + bar.get_height()/2, f'{lat} ms\n({lat/1262*100:.1f}%)',
                 va='center', ha='left', fontsize=8.5, color='#2C3E50', fontweight='bold')
    
    # Subplot 2: Total Decision Latency vs HRI Threshold
    total_time = 1.262
    hri_target = 1.500
    
    categories = ['Proposed Framework\n(Decision Latency)', 'HRI Acceptable\nThreshold Limit']
    times = [total_time, hri_target]
    bar_colors = ['#27AE60', '#E74C3C']
    
    b2 = ax2.bar(categories, times, color=bar_colors, width=0.45, edgecolor='#2C3E50', linewidth=1.2)
    ax2.set_ylabel('Total Decision Time (seconds)', fontweight='bold', fontsize=10)
    ax2.set_title('(b) Total Response vs. HRI Target', fontweight='bold', fontsize=10.5, pad=10)
    ax2.set_ylim(0, 2.0)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    
    ax2.axhline(hri_target, color='#C0392B', linestyle='--', linewidth=1.5, alpha=0.8)
    ax2.text(0.5, hri_target + 0.05, 'Max HRI Lag (1.50 s)', color='#C0392B', ha='center', fontsize=8.5, fontweight='bold')
    
    for bar, t in zip(b2, times):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{t:.2f} s',
                 ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#1A252F')
    
    plt.tight_layout()
    out = os.path.join(IMAGES_DIR, "figure4_latency_chart.png")
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {out}")

def generate_figure5_position_error_chart():
    """Generates Cartesian positioning error chart vs physical suction cup limit and VLA."""
    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=300)
    
    runs = ['Run 1\n(Red)', 'Run 2\n(Yellow)', 'Run 3\n(Blue)', 'Run 4\n(Red)', 'Run 5\n(Yellow)', 'Overall\nMean']
    errors = [3.20, 2.90, 3.40, 2.80, 3.60, 3.18]
    bar_colors = ['#2980B9', '#2980B9', '#2980B9', '#2980B9', '#2980B9', '#16A085']
    
    bars = ax.bar(runs, errors, color=bar_colors, width=0.52, edgecolor='#1B2631', linewidth=1.1, zorder=3)
    
    # Error bar on overall mean
    ax.errorbar(5, 3.18, yerr=0.33, fmt='none', ecolor='#111111', capsize=5, capthick=1.5, elinewidth=1.5, zorder=4)
    
    # Add Threshold Lines
    r_cup = 8.0
    vla_err = 15.0
    
    ax.axhline(r_cup, color='#27AE60', linestyle='--', linewidth=1.8, label=r'Suction Cup Effective Radius ($r_{\mathrm{cup}} = 8.0$ mm)', zorder=2)
    ax.axhline(vla_err, color='#C0392B', linestyle='-.', linewidth=1.8, label=r'Typical VLA Positioning Error ($\sim 15.0$ mm)', zorder=2)
    
    # Fill safe region
    ax.axhspan(0, r_cup, facecolor='#E8F8F5', alpha=0.5, label='Airtight Vacuum Sealing Safe Zone')
    
    ax.set_ylabel('Cartesian Positioning Error (mm)', fontweight='bold', fontsize=10.5)
    ax.set_title('Physical Cartesian Positioning Precision across 5 Baseline Trials vs. Operational Tolerances', fontweight='bold', fontsize=11, pad=12)
    ax.set_ylim(0, 18.0)
    ax.grid(axis='y', linestyle=':', alpha=0.6, zorder=1)
    
    for bar, val in zip(bars, errors):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.35, f'{val:.2f} mm',
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1A252C')
    
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, fontsize=8.5)
    
    plt.tight_layout()
    out = os.path.join(IMAGES_DIR, "figure5_position_error_chart.png")
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {out}")

def generate_figure6_vla_radar_chart():
    """Generates multi-metric Spider/Radar comparison chart."""
    categories = [
        'Cartesian\nPrecision',
        'Deterministic\nSafety',
        'Computational\nEfficiency',
        'Decision\nSpeed',
        'Controller EKI\nCompatibility',
        'Vocabulary\nFlexibility'
    ]
    N = len(categories)
    
    # Scores (1 to 10 scale)
    # Proposed ROS 2: Precision(9.5), Safety(9.8), Efficiency(9.5), Latency(8.8), EKI(9.8), Vocabulary(6.0)
    # VLA Models:     Precision(4.0), Safety(4.5), Efficiency(3.0), Latency(6.0), EKI(4.0), Vocabulary(9.8)
    scores_proposed = [9.5, 9.8, 9.5, 8.8, 9.8, 6.0]
    scores_vla = [4.0, 4.5, 3.0, 6.0, 4.0, 9.8]
    
    # Close polygon
    scores_proposed += scores_proposed[:1]
    scores_vla += scores_vla[:1]
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6.2, 5.5), subplot_kw=dict(polar=True), dpi=300)
    
    plt.xticks(angles[:-1], categories, color='#2C3E50', size=9.5, fontweight='bold')
    ax.set_rlabel_position(25)
    plt.yticks([2, 4, 6, 8, 10], ["2", "4", "6", "8", "10"], color="#7F8C8D", size=7.5)
    plt.ylim(0, 10.5)
    
    # Plot Proposed
    ax.plot(angles, scores_proposed, linewidth=2.2, linestyle='solid', color='#2980B9', label='Proposed Modular ROS 2 Framework')
    ax.fill(angles, scores_proposed, color='#3498DB', alpha=0.35)
    
    # Plot VLA
    ax.plot(angles, scores_vla, linewidth=2.2, linestyle='dashed', color='#E74C3C', label='End-to-End VLA Models (OpenVLA / Octo)')
    ax.fill(angles, scores_vla, color='#E74C3C', alpha=0.20)
    
    plt.title('Multi-Metric Paradigm Comparison:\nModular ROS 2 Architecture vs. Vision-Language-Action Models',
              size=11, fontweight='bold', color='#1B365D', pad=22)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=True, facecolor='white', fontsize=9)
    
    plt.tight_layout()
    out = os.path.join(IMAGES_DIR, "figure6_vla_radar_chart.png")
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {out}")

if __name__ == "__main__":
    generate_figure4_latency_chart()
    generate_figure5_position_error_chart()
    generate_figure6_vla_radar_chart()
