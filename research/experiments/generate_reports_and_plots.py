"""
M7 Research Reporting & Visualization Generator (Matplotlib-Only)
================================================================
SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 7: Quantitative Research Evaluation Framework

Generates:
- Structured Markdown & CSV Tables (research/results/tables/)
- Publication-Grade Figures via Matplotlib Only (research/results/figures/)

Strict Rules:
- Only generates visual plots when valid result summary files exist.
- Never hardcodes or fabricates data points.
- Prominently labels development fixture results when applicable.
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/CLI execution
import matplotlib.pyplot as plt


def generate_tables_and_plots(
    summary_path: Path,
    tables_dir: Path,
    figures_dir: Path,
) -> None:
    """Reads processed summary and outputs tables and figures."""
    if not summary_path.exists():
        print(f"Error: Summary file {summary_path} does not exist.")
        return

    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    is_fixture = data.get("benchmark_metadata", {}).get("is_development_fixture", False)
    fixture_tag = "\n> [!NOTE]\n> **DEVELOPMENT FIXTURE — NOT RESEARCH RESULT.** Data generated on test fixtures.\n\n" if is_fixture else ""

    # -------------------------------------------------------------------------
    # 1. Overall Generation Comparison Table (Markdown & CSV)
    # -------------------------------------------------------------------------
    t1 = data.get("track_1_generation_quality", {})
    desc = t1.get("descriptive_statistics", {})

    md_table_1 = f"# M7 Benchmark: Track 1 Generation Quality Comparison\n{fixture_tag}"
    md_table_1 += "| Method | Architecture | Mean FSCR | Median FSCR | Std Dev | Sample Size |\n"
    md_table_1 += "| :--- | :--- | :---: | :---: | :---: | :---: |\n"

    csv_rows_1 = [["Method", "Architecture", "Mean_FSCR", "Median_FSCR", "Std_Dev", "Sample_Size"]]

    method_labels = {
        "METHOD_A": "Direct LLM Prompting",
        "METHOD_B": "Basic RAG (pgvector)",
        "METHOD_C": "RAG + Context Normalization",
    }

    for m_key, m_name in method_labels.items():
        stats = desc.get(m_key, {})
        mean_v = stats.get("mean", "N/A")
        med_v = stats.get("median", "N/A")
        std_v = stats.get("std", "N/A")
        n_v = stats.get("n", 0)
        md_table_1 += f"| **{m_key}** | {m_name} | {mean_v} | {med_v} | {std_v} | {n_v} |\n"
        csv_rows_1.append([m_key, m_name, str(mean_v), str(med_v), str(std_v), str(n_v)])

    with open(tables_dir / "track1_generation_comparison.md", "w", encoding="utf-8") as f:
        f.write(md_table_1)

    with open(tables_dir / "track1_generation_comparison.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows_1)

    # -------------------------------------------------------------------------
    # 2. Track 2 Verification Classification Report Table
    # -------------------------------------------------------------------------
    t2 = data.get("track_2_verification_quality")
    if t2:
        md_table_2 = f"# M7 Benchmark: Track 2 Verification Agent Quality\n{fixture_tag}"
        md_table_2 += f"**Macro-F1**: {t2.get('macro_f1')} | **Macro-Precision**: {t2.get('macro_precision')} | **Macro-Recall**: {t2.get('macro_recall')}\n\n"
        md_table_2 += "| Gold Verdict Class | Support | Precision | Recall | F1 Score |\n"
        md_table_2 += "| :--- | :---: | :---: | :---: | :---: |\n"

        csv_rows_2 = [["Verdict_Class", "Support", "Precision", "Recall", "F1_Score"]]

        for cls_name, metrics in t2.get("per_class", {}).items():
            sup = metrics.get("support", 0)
            prec = metrics.get("precision", 0.0)
            rec = metrics.get("recall", 0.0)
            f1 = metrics.get("f1_score", 0.0)
            md_table_2 += f"| `{cls_name}` | {sup} | {prec} | {rec} | **{f1}** |\n"
            csv_rows_2.append([cls_name, str(sup), str(prec), str(rec), str(f1)])

        with open(tables_dir / "track2_verification_report.md", "w", encoding="utf-8") as f:
            f.write(md_table_2)

        with open(tables_dir / "track2_verification_report.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows_2)

    # -------------------------------------------------------------------------
    # 3. Track 3 Operational Latency Table
    # -------------------------------------------------------------------------
    t3 = data.get("track_3_operational_telemetry", {})
    latencies = t3.get("method_latencies_ms", {})

    md_table_3 = f"# M7 Benchmark: Operational Latency Comparison\n{fixture_tag}"
    md_table_3 += f"> *Notice: {t3.get('method_d_notice')}*\n\n"
    md_table_3 += "| Pipeline Method | Mean Wall-Clock Latency (ms) |\n"
    md_table_3 += "| :--- | :---: |\n"
    for m_k, lat_v in latencies.items():
        md_table_3 += f"| **{m_k.replace('_mean', '')}** | {lat_v} ms |\n"

    with open(tables_dir / "operational_latency_comparison.md", "w", encoding="utf-8") as f:
        f.write(md_table_3)

    # -------------------------------------------------------------------------
    # 4. Matplotlib Visualizations (Matplotlib ONLY)
    # -------------------------------------------------------------------------
    # Plot 1: Track 1 Generation Quality (Method vs FSCR)
    methods = ["Method A\n(Direct)", "Method B\n(Basic RAG)", "Method C\n(RAG + Norm)"]
    means = [
        desc.get("METHOD_A", {}).get("mean", 0.0) or 0.0,
        desc.get("METHOD_B", {}).get("mean", 0.0) or 0.0,
        desc.get("METHOD_C", {}).get("mean", 0.0) or 0.0,
    ]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(methods, means, color=["#64748b", "#3b82f6", "#10b981"], width=0.5)
    plt.ylabel("Fully Supported Claim Rate (FSCR)", fontsize=11)
    plt.title(
        f"Track 1: Generation Architecture Progression vs FSCR\n{'[DEVELOPMENT FIXTURE]' if is_fixture else ''}",
        fontsize=12,
        fontweight="bold",
    )
    plt.ylim(0.0, 1.1)
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.03, f"{yval:.2f}", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plt.savefig(figures_dir / "track1_method_vs_fscr.png", dpi=300)
    plt.savefig(figures_dir / "track1_method_vs_fscr.svg")
    plt.close()

    # Plot 2: Track 2 Confusion Matrix Heatmap (via Matplotlib imshow)
    if t2 and "confusion_matrix" in t2:
        classes = ["SUPPORTED", "CONTRADICTED", "PART_SUPP", "INSUFFICIENT"]
        raw_classes = ["SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE"]
        cm_data = []
        for g_cls in raw_classes:
            row = [t2["confusion_matrix"].get(g_cls, {}).get(p_cls, 0) for p_cls in raw_classes]
            cm_data.append(row)

        plt.figure(figsize=(7, 6))
        plt.imshow(cm_data, interpolation="nearest", cmap=plt.cm.Blues)
        plt.title(
            f"Track 2: Verification Agent Confusion Matrix\n{'[DEVELOPMENT FIXTURE]' if is_fixture else ''}",
            fontsize=12,
            fontweight="bold",
        )
        plt.colorbar()
        tick_marks = range(len(classes))
        plt.xticks(tick_marks, classes, rotation=35, ha="right", fontsize=9)
        plt.yticks(tick_marks, classes, fontsize=9)
        plt.xlabel("Predicted Verdict", fontsize=10, fontweight="bold")
        plt.ylabel("Gold Ground-Truth Verdict", fontsize=10, fontweight="bold")

        # Add text annotations inside cells
        for i in range(len(raw_classes)):
            for j in range(len(raw_classes)):
                val = cm_data[i][j]
                color = "white" if val > 2 else "black"
                plt.text(j, i, str(val), ha="center", va="center", color=color, fontweight="bold", fontsize=11)

        plt.tight_layout()
        plt.savefig(figures_dir / "track2_verification_confusion_matrix.png", dpi=300)
        plt.savefig(figures_dir / "track2_verification_confusion_matrix.svg")
        plt.close()

    # Plot 3: Operational Latency across A, B, C, D
    lat_keys = ["METHOD_A_mean", "METHOD_B_mean", "METHOD_C_mean", "METHOD_D_mean"]
    lat_labels = ["Method A\n(Direct)", "Method B\n(Basic RAG)", "Method C\n(RAG+Norm)", "Method D\n(RAG+Norm+Verif)"]
    lat_vals = [latencies.get(k, 0.0) for k in lat_keys]

    plt.figure(figsize=(9, 5))
    lat_bars = plt.bar(lat_labels, lat_vals, color=["#64748b", "#3b82f6", "#10b981", "#8b5cf6"], width=0.55)
    plt.ylabel("End-to-End Latency (ms)", fontsize=11)
    plt.title(
        f"Track 3: System Pipeline Latency Comparison\n{'[DEVELOPMENT FIXTURE]' if is_fixture else ''}",
        fontsize=12,
        fontweight="bold",
    )
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    for bar in lat_bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 5, f"{yval:.1f} ms", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plt.savefig(figures_dir / "track3_operational_latency.png", dpi=300)
    plt.savefig(figures_dir / "track3_operational_latency.svg")
    plt.close()

    print(f"Reports and figures successfully generated in:\n - Tables: {tables_dir}\n - Figures: {figures_dir}")


if __name__ == "__main__":
    s_path = ROOT_DIR / "research" / "results" / "processed" / "m7_evaluation_summary.json"
    t_dir = ROOT_DIR / "research" / "results" / "tables"
    f_dir = ROOT_DIR / "research" / "results" / "figures"
    generate_tables_and_plots(s_path, t_dir, f_dir)
