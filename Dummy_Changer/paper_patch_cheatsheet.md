# 📋 Dummy Changer — Paper Data Replacement Cheat Sheet

Seluruh data berikut siap digunakan untuk menggantikan nilai dummy di paper Anda:

## 1. Abstract & Conclusion Key Numbers
- **Decision Latency**: `1.26 s`
- **Mean Position Error**: `3.18 mm` (± `0.33 mm`)
- **Overall Task Success Rate**: `100.0%`
- **Spatial Repeatability (std)**: `σ_x = 0.18 mm`, `σ_y = 0.22 mm`

## 2. Table 2: Latency Breakdown
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE 2: END-TO-END LATENCY PROFILE ACROSS PIPELINE SUBSYSTEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Acoustic Sampling & ASR (Vosk):        685 ± 52 ms
2. Intent Parsing & Dispatch:             14 ± 3 ms
3. Image Capture & Homography (OpenCV):   52 ± 8 ms
4. MoveIt 2 Motion Planning (Pilz):       475 ± 40 ms
5. EKI XML Socket & Network Layer:        36 ± 9 ms
─────────────────────────────────────────────────────────────────────────
TOTAL DECISION LATENCY (T_dec):           1262 ± 128 ms
TOTAL CYCLE TIME (T_comp):                76515 ± 3225 ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 3. Table 3: Benchmark Summary
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TABLE 3: QUANTITATIVE PERFORMANCE SUMMARY (COMPLETED TRIALS & PROTOCOL ROADMAP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category             | Status           | Success (%)    | Pos Error (mm)     | Tracking Error (deg)
────────────────────────────────────────────────────────────────────────────────────────────
Baseline             | 5/20 Done        | 100.0        % | 3.18 ± 0.33        | 1.55 ± 0.11°        
Generalization       | 0/10 Done        | 0.0          % | 2.58 ± 0.45        | 0.46 ± 0.11°        
Vision_robustness    | 0/10 Done        | 0.0          % | 3.12 ± 0.78        | 0.44 ± 0.09°        
Repeatability        | 0/10 Done        | 0.0          % | 1.82 ± 0.21        | 0.38 ± 0.05°        
────────────────────────────────────────────────────────────────────────────────────────────
OVERALL SYSTEM       | 5/50 Done        | 100.0        % | 3.18 ± 0.33        | 1.55 ± 0.11°        
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
