"""
Microstrip Patch Antenna Design Studio – Version 2.0
-----------------------------------------------------
Calculates rectangular microstrip patch antenna dimensions using
standard transmission-line model equations.

Upgrades in Version 2.0:
- Multiple Substrate Material Selection (FR4, Rogers RO4003C, Rogers RT/duroid 5880, Custom)
- Frequency Sweep Analysis (Width & Length vs. Frequency with interactive plots & CSV export)
- Engineering PDF Design Report Generation (with actual calculations, equations, summaries, & charts)
- Refined Navy Blue, White, and Cyan UI theme with tabbed layout and input validations

Author : Antenna Design Studio
Version: 2.0.0
"""

import os
import tempfile
# Ensure Matplotlib config directory is accessible in restricted/sandboxed environments
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import io
import csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Streamlit
import streamlit as st

# PDF generation imports via ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# ─────────────────────────────────────────────
#  SUBSTRATE MATERIAL DATABASE
# ─────────────────────────────────────────────
SUBSTRATE_DATABASE = {
    "FR4": {
        "eps_r": 4.4,
        "default_h_mm": 1.6,
        "loss_tangent": "0.020",
        "description": "Standard woven glass-reinforced epoxy laminate. Cost-effective, popular for sub-6 GHz prototyping and hobbyist RF.",
    },
    "Rogers RO4003C": {
        "eps_r": 3.55,
        "default_h_mm": 0.813,
        "loss_tangent": "0.0027",
        "description": "Ceramic-filled hydrocarbon/thermoset laminate with low dielectric loss and stable high-frequency characteristics.",
    },
    "Rogers RT/duroid 5880": {
        "eps_r": 2.20,
        "default_h_mm": 0.787,
        "loss_tangent": "0.0009",
        "description": "PTFE glass microfiber composite offering minimal dielectric loss and superior high-frequency performance up to Ku-band.",
    },
    "Custom Material": {
        "eps_r": 4.40,
        "default_h_mm": 1.60,
        "loss_tangent": "User Specified",
        "description": "User-defined substrate parameters. Enter relative permittivity and substrate thickness manually.",
    },
}

# ─────────────────────────────────────────────
#  ANTENNA DESIGN EQUATIONS (SI UNITS INTERNALLY)
# ─────────────────────────────────────────────

def speed_of_light() -> float:
    """Returns speed of light in vacuum in m/s."""
    return 3e8


def calc_patch_width(freq_hz: float, eps_r: float) -> float:
    """
    Patch Width (W) [metres]
    W = c / (2 * f) * sqrt(2 / (eps_r + 1))
    """
    if freq_hz <= 0 or eps_r < 1.0:
        raise ValueError("Frequency must be > 0 and eps_r must be >= 1.0.")
    c = speed_of_light()
    return (c / (2.0 * freq_hz)) * np.sqrt(2.0 / (eps_r + 1.0))


def calc_effective_dielectric(eps_r: float, h: float, W: float) -> float:
    """
    Effective dielectric constant (eps_eff)
    eps_eff = (eps_r + 1)/2 + (eps_r - 1)/2 * (1 + 12*h/W)^(-0.5)
    Valid for microstrip lines when W/h > 1.
    """
    if W <= 0 or h <= 0:
        raise ValueError("Width W and thickness h must be strictly positive.")
    ratio = h / W
    return (eps_r + 1.0) / 2.0 + ((eps_r - 1.0) / 2.0) * ((1.0 + 12.0 * ratio) ** (-0.5))


def calc_delta_L(eps_eff: float, h: float, W: float) -> float:
    """
    Fringing length extension (ΔL) [metres]
    ΔL = 0.412 * h * (eps_eff + 0.3) * (W/h + 0.264)
                    / ((eps_eff - 0.258) * (W/h + 0.8))
    """
    if h <= 0 or W <= 0:
        raise ValueError("Thickness h and width W must be strictly positive.")
    ratio = W / h
    numerator = (eps_eff + 0.3) * (ratio + 0.264)
    denominator = (eps_eff - 0.258) * (ratio + 0.8)
    if denominator <= 0:
        denominator = 1e-9
    return 0.412 * h * (numerator / denominator)


def calc_effective_length(freq_hz: float, eps_eff: float) -> float:
    """
    Effective patch length (L_eff) [metres]
    L_eff = c / (2 * f * sqrt(eps_eff))
    """
    if freq_hz <= 0 or eps_eff <= 0:
        raise ValueError("Frequency and eps_eff must be strictly positive.")
    c = speed_of_light()
    return c / (2.0 * freq_hz * np.sqrt(eps_eff))


def calc_physical_length(L_eff: float, delta_L: float) -> float:
    """
    Physical patch length (L) [metres]
    L = L_eff - 2 * ΔL
    """
    return L_eff - 2.0 * delta_L


def design_antenna(freq_ghz: float, eps_r: float, h_mm: float) -> dict:
    """
    Run full antenna design and return a dictionary with all parameters in SI and mm.
    """
    if freq_ghz <= 0:
        raise ValueError("Frequency must be greater than 0 GHz.")
    if eps_r < 1.0:
        raise ValueError("Relative permittivity must be >= 1.0.")
    if h_mm <= 0:
        raise ValueError("Substrate thickness must be greater than 0 mm.")

    freq_hz = freq_ghz * 1e9
    h_m = h_mm * 1e-3

    W = calc_patch_width(freq_hz, eps_r)
    eps_eff = calc_effective_dielectric(eps_r, h_m, W)
    dL = calc_delta_L(eps_eff, h_m, W)
    L_eff = calc_effective_length(freq_hz, eps_eff)
    L = calc_physical_length(L_eff, dL)
    lambda_0_m = speed_of_light() / freq_hz

    return {
        "freq_ghz": freq_ghz,
        "eps_r": eps_r,
        "h_mm": h_mm,
        "W_mm": W * 1e3,
        "eps_eff": eps_eff,
        "dL_mm": dL * 1e3,
        "L_eff_mm": L_eff * 1e3,
        "L_mm": L * 1e3,
        "lambda_mm": lambda_0_m * 1e3,
    }


def run_frequency_sweep(
    f_start: float, f_stop: float, f_step: float, eps_r: float, h_mm: float
) -> pd.DataFrame:
    """
    Calculates antenna dimensions across a sweep of frequency points.
    Returns a pandas DataFrame.
    """
    num_steps = int(round((f_stop - f_start) / f_step)) + 1
    freqs = np.linspace(f_start, f_stop, num_steps)

    rows = []
    for f in freqs:
        res = design_antenna(float(f), eps_r, h_mm)
        rows.append({
            "Frequency (GHz)": round(float(f), 4),
            "Patch Width W (mm)": round(res["W_mm"], 4),
            "Effective εr": round(res["eps_eff"], 6),
            "Fringing Extension ΔL (mm)": round(res["dL_mm"], 4),
            "Effective Length Leff (mm)": round(res["L_eff_mm"], 4),
            "Physical Length L (mm)": round(res["L_mm"], 4),
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
#  INPUT VALIDATIONS
# ─────────────────────────────────────────────

def validate_inputs(freq_ghz: float, eps_r: float, h_mm: float) -> list:
    """Validates single-frequency design inputs."""
    errors = []
    if freq_ghz <= 0:
        errors.append("❌ Target Frequency must be a positive number greater than 0 GHz.")
    elif freq_ghz > 100:
        errors.append("❌ Target Frequency above 100 GHz exceeds standard planar microstrip domain.")

    if eps_r < 1.0:
        errors.append("❌ Substrate dielectric constant (εᵣ) must be ≥ 1.0 (vacuum = 1.0).")
    elif eps_r > 100.0:
        errors.append("❌ Substrate dielectric constant (εᵣ) > 100 is unusually high for practical microwave substrates.")

    if h_mm <= 0:
        errors.append("❌ Substrate thickness h must be greater than 0 mm.")
    elif h_mm > 25.0:
        errors.append("❌ Substrate thickness h > 25 mm is excessively thick for planar microstrip antennas.")

    return errors


def validate_sweep_inputs(f_start: float, f_stop: float, f_step: float) -> list:
    """Validates frequency sweep inputs."""
    errors = []
    if f_start <= 0:
        errors.append("❌ Start Frequency must be greater than 0 GHz.")
    if f_stop <= 0:
        errors.append("❌ Stop Frequency must be greater than 0 GHz.")
    if f_stop <= f_start:
        errors.append("❌ Stop Frequency must be strictly greater than Start Frequency.")
    if f_step <= 0:
        errors.append("❌ Frequency Step must be greater than 0 GHz.")
    else:
        num_points = int(round((f_stop - f_start) / f_step)) + 1
        if num_points < 2:
            errors.append("❌ Frequency sweep must contain at least 2 calculation points.")
        elif num_points > 500:
            errors.append(f"❌ Sweep produces {num_points} points (maximum allowed is 500). Please increase the frequency step.")
    return errors


# ─────────────────────────────────────────────
#  MATPLOTLIB VISUALIZATIONS
# ─────────────────────────────────────────────

def draw_patch_diagram(W_mm: float, L_mm: float, h_mm: float, for_report: bool = False) -> plt.Figure:
    """
    Draw a top-view rectangular patch diagram with dimension annotations.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=120)

    if for_report:
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8fafc")
        gp_color = "#e2e8f0"
        gp_edge = "#64748b"
        sub_color = "#f1f5f9"
        text_w_color = "#0369a1"
        text_l_color = "#047857"
        title_color = "#0f172a"
        sub_txt_color = "#64748b"
    else:
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#0f172a")
        gp_color = "#1e293b"
        gp_edge = "#334155"
        sub_color = "#162035"
        text_w_color = "#38bdf8"
        text_l_color = "#34d399"
        title_color = "#f1f5f9"
        sub_txt_color = "#94a3b8"

    pad_x = W_mm * 0.35
    pad_y = L_mm * 0.40

    # Ground plane backdrop
    gp = mpatches.FancyBboxPatch(
        (-pad_x, -pad_y),
        W_mm + 2 * pad_x,
        L_mm + 2 * pad_y,
        boxstyle="round,pad=0",
        linewidth=1.2,
        edgecolor=gp_edge,
        facecolor=gp_color,
    )
    ax.add_patch(gp)

    # Substrate hint
    sub = mpatches.FancyBboxPatch(
        (-pad_x * 0.6, -pad_y * 0.6),
        W_mm + 1.2 * pad_x,
        L_mm + 1.2 * pad_y,
        boxstyle="round,pad=0",
        linewidth=0,
        facecolor=sub_color,
        alpha=0.7,
    )
    ax.add_patch(sub)

    # Radiating patch (gold / copper metallic look)
    patch_rect = mpatches.FancyBboxPatch(
        (0, 0),
        W_mm,
        L_mm,
        boxstyle="round,pad=0.2",
        linewidth=2,
        edgecolor="#f59e0b",
        facecolor="#d97706",
        alpha=0.92,
    )
    ax.add_patch(patch_rect)

    # Feed point indicator
    ax.plot(W_mm / 2.0, L_mm * 0.18, "o", color="#ef4444", markersize=7, zorder=5)
    ax.text(
        W_mm / 2.0 + W_mm * 0.05,
        L_mm * 0.18,
        "Coaxial / Inset Feed",
        color="#ef4444",
        fontsize=8,
        fontweight="bold",
        va="center",
    )

    # Width annotation (horizontal)
    arrow_y = -pad_y * 0.45
    ax.annotate(
        "",
        xy=(W_mm, arrow_y),
        xytext=(0, arrow_y),
        arrowprops=dict(arrowstyle="<->", color=text_w_color, lw=1.6),
    )
    ax.text(
        W_mm / 2.0,
        arrow_y - pad_y * 0.18,
        f"Width W = {W_mm:.2f} mm",
        ha="center",
        va="top",
        color=text_w_color,
        fontsize=9.5,
        fontweight="bold",
    )

    # Length annotation (vertical)
    arrow_x = W_mm + pad_x * 0.45
    ax.annotate(
        "",
        xy=(arrow_x, L_mm),
        xytext=(arrow_x, 0),
        arrowprops=dict(arrowstyle="<->", color=text_l_color, lw=1.6),
    )
    ax.text(
        arrow_x + pad_x * 0.18,
        L_mm / 2.0,
        f"Length L = {L_mm:.2f} mm",
        ha="left",
        va="center",
        color=text_l_color,
        fontsize=9.5,
        fontweight="bold",
        rotation=90,
    )

    # Substrate label
    ax.text(
        -pad_x * 0.55,
        -pad_y * 0.55,
        f"Ground Plane / Substrate (h = {h_mm:.2f} mm)",
        color=sub_txt_color,
        fontsize=7.5,
        va="top",
    )

    ax.set_xlim(-pad_x, W_mm + pad_x * 1.5)
    ax.set_ylim(-pad_y * 1.25, L_mm + pad_y)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        "Rectangular Patch Antenna — Top View Geometry",
        color=title_color,
        fontsize=11.5,
        fontweight="bold",
        pad=12,
    )

    fig.tight_layout()
    return fig


def draw_comparison_chart(
    W_mm: float, L_mm: float, L_eff_mm: float, dL_mm: float, for_report: bool = False
) -> plt.Figure:
    """
    Horizontal bar chart comparing patch physical and electrical dimensions.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=120)

    if for_report:
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8fafc")
        title_color = "#0f172a"
        label_color = "#334155"
        val_color = "#0f172a"
        grid_color = "#cbd5e1"
        spine_color = "#94a3b8"
        colors_list = ["#0284c7", "#059669", "#d97706", "#dc2626"]
    else:
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#0f172a")
        title_color = "#f1f5f9"
        label_color = "#94a3b8"
        val_color = "#e2e8f0"
        grid_color = "#1e293b"
        spine_color = "#334155"
        colors_list = ["#38bdf8", "#34d399", "#fbbf24", "#f87171"]

    labels = ["Width (W)", "Physical Length (L)", "Effective Length (Leff)", "Fringe Extension (ΔL)"]
    values = [W_mm, L_mm, L_eff_mm, dL_mm]

    bars = ax.barh(labels, values, color=colors_list, edgecolor=spine_color, height=0.5, linewidth=0.8)

    max_v = max(values) if values else 1.0
    for bar, val in zip(bars, values):
        ax.text(
            val + max_v * 0.02,
            bar.get_y() + bar.get_height() / 2.0,
            f"{val:.3f} mm",
            va="center",
            color=val_color,
            fontsize=8.5,
            fontweight="bold",
        )

    ax.set_xlabel("Dimension (mm)", color=label_color, fontsize=9.5)
    ax.set_title("Key Antenna Dimension Breakdown", color=title_color, fontsize=11.5, fontweight="bold")
    ax.tick_params(colors=label_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(spine_color)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, max_v * 1.25)
    ax.grid(axis="x", color=grid_color, linestyle="--", alpha=0.6)

    fig.tight_layout()
    return fig


def draw_frequency_vs_width_plot(sweep_df: pd.DataFrame, for_report: bool = False) -> plt.Figure:
    """
    Generates Graph 1: Frequency vs Patch Width.
    """
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=120)

    if for_report:
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8fafc")
        line_color = "#0284c7"
        marker_color = "#0369a1"
        title_color = "#0f172a"
        label_color = "#334155"
        grid_color = "#cbd5e1"
        spine_color = "#94a3b8"
    else:
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#0f172a")
        line_color = "#00e5ff"
        marker_color = "#38bdf8"
        title_color = "#f1f5f9"
        label_color = "#94a3b8"
        grid_color = "#1e293b"
        spine_color = "#334155"

    ax.plot(
        sweep_df["Frequency (GHz)"],
        sweep_df["Patch Width W (mm)"],
        marker="o",
        markersize=4,
        linewidth=2,
        color=line_color,
        markerfacecolor=marker_color,
        label="Patch Width (W)",
    )

    ax.set_xlabel("Frequency (GHz)", color=label_color, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Patch Width W (mm)", color=label_color, fontsize=9.5, fontweight="bold")
    ax.set_title("Frequency vs. Patch Width (W)", color=title_color, fontsize=11, fontweight="bold")
    ax.tick_params(colors=label_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(spine_color)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(color=grid_color, linestyle="--", alpha=0.6)

    fig.tight_layout()
    return fig


def draw_frequency_vs_length_plot(sweep_df: pd.DataFrame, for_report: bool = False) -> plt.Figure:
    """
    Generates Graph 2: Frequency vs Physical Patch Length.
    """
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=120)

    if for_report:
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8fafc")
        line_color = "#059669"
        marker_color = "#047857"
        title_color = "#0f172a"
        label_color = "#334155"
        grid_color = "#cbd5e1"
        spine_color = "#94a3b8"
    else:
        fig.patch.set_facecolor("#0b0f19")
        ax.set_facecolor("#0f172a")
        line_color = "#34d399"
        marker_color = "#10b981"
        title_color = "#f1f5f9"
        label_color = "#94a3b8"
        grid_color = "#1e293b"
        spine_color = "#334155"

    ax.plot(
        sweep_df["Frequency (GHz)"],
        sweep_df["Physical Length L (mm)"],
        marker="s",
        markersize=4,
        linewidth=2,
        color=line_color,
        markerfacecolor=marker_color,
        label="Physical Length (L)",
    )

    ax.set_xlabel("Frequency (GHz)", color=label_color, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Physical Patch Length L (mm)", color=label_color, fontsize=9.5, fontweight="bold")
    ax.set_title("Frequency vs. Physical Patch Length (L)", color=title_color, fontsize=11, fontweight="bold")
    ax.tick_params(colors=label_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(spine_color)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(color=grid_color, linestyle="--", alpha=0.6)

    fig.tight_layout()
    return fig


def fig_to_png_bytes(fig: plt.Figure) -> bytes:
    """Converts a Matplotlib figure into PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=140)
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────
#  CSV EXPORT HELPERS
# ─────────────────────────────────────────────

def generate_single_csv(results: dict, material_name: str) -> bytes:
    """Generates CSV bytes for single-frequency design."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["MICROSTRIP PATCH ANTENNA DESIGN STUDIO – VERSION 2.0"])
    writer.writerow(["Parameter", "Value", "Unit", "Type / Classification"])
    writer.writerow(["Substrate Material", material_name, "—", "Input Specification"])
    writer.writerow(["Design Frequency (f0)", f"{results['freq_ghz']:.4f}", "GHz", "Operating Parameter"])
    writer.writerow(["Substrate Dielectric Constant (eps_r)", f"{results['eps_r']:.4f}", "—", "Material Property (Nominal)"])
    writer.writerow(["Substrate Thickness (h)", f"{results['h_mm']:.4f}", "mm", "Physical Geometry"])
    writer.writerow(["Free-Space Wavelength (lambda_0)", f"{results['lambda_mm']:.4f}", "mm", "Derived Constant"])
    writer.writerow(["Patch Width (W)", f"{results['W_mm']:.4f}", "mm", "Calculated Radiating Dimension"])
    writer.writerow(["Effective Dielectric Constant (eps_eff)", f"{results['eps_eff']:.6f}", "—", "Calculated Field Parameter"])
    writer.writerow(["Fringing Length Extension (delta_L)", f"{results['dL_mm']:.4f}", "mm", "Calculated Fringing Parameter"])
    writer.writerow(["Effective Patch Length (L_eff)", f"{results['L_eff_mm']:.4f}", "mm", "Resonant Half-Wavelength"])
    writer.writerow(["Physical Patch Length (L)", f"{results['L_mm']:.4f}", "mm", "Synthesized Copper Dimension"])
    writer.writerow([])
    writer.writerow(["DISCLAIMER", "Results are theoretical estimations based on the standard Transmission-Line Model."])
    writer.writerow(["NOTE", "EM simulation (HFSS/CST) and physical fabrication tuning recommended for final deployment."])
    return output.getvalue().encode("utf-8")


def generate_sweep_csv(sweep_df: pd.DataFrame, material_name: str, eps_r: float, h_mm: float) -> bytes:
    """Generates CSV bytes for frequency sweep analysis."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["MICROSTRIP PATCH ANTENNA DESIGN STUDIO – FREQUENCY SWEEP ANALYSIS"])
    writer.writerow(["Substrate Material", material_name])
    writer.writerow(["Nominal Dielectric Constant (eps_r)", f"{eps_r:.4f}"])
    writer.writerow(["Substrate Thickness h (mm)", f"{h_mm:.4f}"])
    writer.writerow([])
    output.write(sweep_df.to_csv(index=False))
    return output.getvalue().encode("utf-8")


# ─────────────────────────────────────────────
#  PDF DESIGN REPORT GENERATOR (REPORTLAB)
# ─────────────────────────────────────────────

class NumberedCanvas(canvas.Canvas):
    """Adds running headers and two-pass page numbers: Page X of Y."""

    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 11 * inch - 26, "Microstrip Patch Antenna Design Studio – Version 2.0 | Design Report")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 30, 8.5 * inch - 36, 11 * inch - 30)

        # Running footer
        footer_text = f"Page {self._pageNumber} of {page_count}  •  Transmission-Line Synthesis Model"
        self.drawRightString(8.5 * inch - 36, 22, footer_text)
        self.drawString(36, 22, "Theoretical estimate. EM simulation & physical tuning recommended for hardware fabrication.")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 31, 8.5 * inch - 36, 31)
        self.restoreState()


def build_pdf_report(
    single_res: dict,
    material_info: dict,
    sweep_df: pd.DataFrame = None,
    patch_img_bytes: bytes = None,
    bar_img_bytes: bytes = None,
    sweep_w_bytes: bytes = None,
    sweep_l_bytes: bytes = None,
) -> bytes:
    """
    Builds an executive engineering PDF design report containing actual calculations,
    material specifications, transmission-line formulas, summary, and rendered figures.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=38,
    )

    styles = getSampleStyleSheet()

    c_primary = colors.HexColor("#0f172a")
    c_accent = colors.HexColor("#0284c7")
    c_dark = colors.HexColor("#1e293b")
    c_light_bg = colors.HexColor("#f8fafc")
    c_muted = colors.HexColor("#64748b")
    c_border = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=c_accent,
        spaceAfter=10,
    )

    h1_style = ParagraphStyle(
        "Heading1Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_dark,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=c_primary,
        spaceAfter=5,
    )

    note_style = ParagraphStyle(
        "NoteCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10.5,
        textColor=c_muted,
        spaceAfter=5,
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("Microstrip Patch Antenna Design Studio – Version 2.0", title_style))
    story.append(Paragraph("Rectangular Microstrip Patch Synthesis & Transmission-Line Analysis Report", subtitle_style))

    # Meta card
    meta_table_data = [
        [
            Paragraph(f"<b>Design Tool:</b> Version 2.0 Studio", body_style),
            Paragraph(f"<b>Target Frequency:</b> {single_res['freq_ghz']:.3f} GHz", body_style),
            Paragraph(f"<b>Substrate:</b> {material_info['name']}", body_style),
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[180, 180, 180])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light_bg),
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # Section 1: Substrate Material & Operating Parameters
    story.append(Paragraph("1. Substrate Material & Specified Operating Parameters", h1_style))
    sub_table_data = [
        ["Parameter", "Symbol", "Specified Value", "Unit / Classification"],
        ["Substrate Material Name", "—", str(material_info["name"]), "Selected Substrate"],
        ["Relative Permittivity (Dielectric Constant)", "εᵣ", f"{single_res['eps_r']:.3f}", "Dimensionless (Nominal)"],
        ["Substrate Thickness", "h", f"{single_res['h_mm']:.3f}", "mm"],
        ["Design Resonant Frequency", "f₀", f"{single_res['freq_ghz']:.3f}", "GHz"],
        ["Free-Space Wavelength", "λ₀", f"{single_res['lambda_mm']:.3f}", "mm"],
    ]
    t_sub = Table(sub_table_data, colWidths=[170, 80, 130, 160])
    t_sub.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_dark),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]))
    story.append(t_sub)
    story.append(Paragraph("<i>Notice: Material properties are nominal catalog values and must be verified against manufacturer datasheets for exact batch tolerances and high-frequency dispersion.</i>", note_style))
    story.append(Spacer(1, 6))

    # Section 2: Calculated Antenna Dimensions
    story.append(Paragraph("2. Synthesized Rectangular Patch Dimensions", h1_style))
    dim_table_data = [
        ["Dimension / Parameter", "Symbol", "Calculated Value", "Unit", "Physical / Electrical Role"],
        ["Patch Width", "W", f"{single_res['W_mm']:.4f}", "mm", "Controls input impedance & radiation efficiency"],
        ["Effective Dielectric Constant", "εeff", f"{single_res['eps_eff']:.6f}", "—", "Composite dielectric value seen by fringing field"],
        ["Fringing Length Extension", "ΔL", f"{single_res['dL_mm']:.4f}", "mm", "Electrical extension due to fringe fields at patch ends"],
        ["Effective Patch Length", "Leff", f"{single_res['L_eff_mm']:.4f}", "mm", "Resonant half-wavelength in effective medium"],
        ["Physical Patch Length", "L", f"{single_res['L_mm']:.4f}", "mm", "Actual fabricated metallic patch length"],
    ]
    t_dim = Table(dim_table_data, colWidths=[140, 50, 95, 45, 210])
    t_dim.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 0), (-1, 0), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
    ]))
    story.append(t_dim)
    story.append(Spacer(1, 6))

    # Section 3: Mathematical Equations
    story.append(Paragraph("3. Transmission-Line Model Formulation", h1_style))
    eq_text = """
    <b>1. Patch Width (W):</b> W = (c / 2f₀) · √(2 / (εᵣ + 1))<br/>
    <b>2. Effective Dielectric Constant (εeff):</b> εeff = (εᵣ + 1)/2 + [(εᵣ − 1)/2] · [1 + 12(h / W)]^(−1/2)<br/>
    <b>3. Fringing Length Extension (ΔL):</b> ΔL = 0.412 · h · [(εeff + 0.3)(W/h + 0.264)] / [(εeff − 0.258)(W/h + 0.8)]<br/>
    <b>4. Effective Patch Length (Leff):</b> Leff = c / [2 · f₀ · √(εeff)]<br/>
    <b>5. Physical Patch Length (L):</b> L = Leff − 2·ΔL<br/>
    <i>Reference: Bahl &amp; Trivedi (1977); C. A. Balanis, Antenna Theory: Analysis and Design (3rd Edition).</i>
    """
    story.append(Paragraph(eq_text, body_style))
    story.append(Spacer(1, 6))

    # Section 4: Design Summary
    story.append(Paragraph("4. Design Summary & Engineering Notes", h1_style))
    summary_text = (
        f"At <b>f₀ = {single_res['freq_ghz']:.3f} GHz</b> on <b>{material_info['name']}</b> "
        f"(nominal εᵣ = {single_res['eps_r']:.2f}, thickness h = {single_res['h_mm']:.2f} mm), "
        f"the synthesized copper patch requires a physical footprint of <b>{single_res['W_mm']:.2f} mm (Width) × "
        f"{single_res['L_mm']:.2f} mm (Length)</b>. "
        f"The resonant patch acts as an open-circuited transmission line of electrical length λ_eff / 2. "
        f"Due to field fringing at both non-radiating edges, the patch appears electrically longer by 2ΔL = "
        f"{2.0 * single_res['dL_mm']:.3f} mm, allowing a physical length reduction to {single_res['L_mm']:.2f} mm. "
        f"Input impedance at the patch edge typically exceeds 200 Ω; an inset microstrip notch or matched coaxial feed "
        f"located at y₀ ≈ L / (2√εeff) is recommended to achieve a standard 50 Ω match."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 6))

    # Section 5: Actual Generated Visualizations
    if patch_img_bytes and bar_img_bytes:
        story.append(Paragraph("5. Synthesized Patch Geometry & Comparison", h1_style))
        img_table = [[
            Image(io.BytesIO(patch_img_bytes), width=265, height=160),
            Image(io.BytesIO(bar_img_bytes), width=265, height=160),
        ]]
        t_img = Table(img_table, colWidths=[270, 270])
        t_img.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t_img)
        story.append(Spacer(1, 8))

    # Section 6: Frequency Sweep Results (if available)
    if sweep_df is not None and not sweep_df.empty:
        story.append(PageBreak())
        story.append(Paragraph("6. Frequency Sweep Analysis", h1_style))
        f_min = sweep_df["Frequency (GHz)"].min()
        f_max = sweep_df["Frequency (GHz)"].max()
        sweep_desc = (
            f"A parametric frequency sweep was computed across the operational band from <b>{f_min:.3f} GHz to {f_max:.3f} GHz</b> "
            f"({len(sweep_df)} sample points). As frequency increases, both patch width and physical length scale inversely with frequency."
        )
        story.append(Paragraph(sweep_desc, body_style))
        story.append(Spacer(1, 6))

        # Sweep plots if provided
        if sweep_w_bytes and sweep_l_bytes:
            sw_img_table = [[
                Image(io.BytesIO(sweep_w_bytes), width=265, height=160),
                Image(io.BytesIO(sweep_l_bytes), width=265, height=160),
            ]]
            t_sw_img = Table(sw_img_table, colWidths=[270, 270])
            t_sw_img.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t_sw_img)
            story.append(Spacer(1, 8))

        # Sweep Table (sample up to 18 points if large)
        display_df = sweep_df
        if len(sweep_df) > 18:
            indices = np.linspace(0, len(sweep_df) - 1, 18, dtype=int)
            display_df = sweep_df.iloc[indices]
            story.append(Paragraph("<i>Representative sample points from sweep:</i>", note_style))

        sw_data = [list(display_df.columns)]
        for _, row in display_df.iterrows():
            sw_data.append([
                f"{row['Frequency (GHz)']:.3f}",
                f"{row['Patch Width W (mm)']:.3f}",
                f"{row['Effective εr']:.4f}",
                f"{row['Fringing Extension ΔL (mm)']:.3f}",
                f"{row['Effective Length Leff (mm)']:.3f}",
                f"{row['Physical Length L (mm)']:.3f}",
            ])
        t_sweep = Table(sw_data, colWidths=[75, 90, 85, 95, 95, 100])
        t_sweep.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_dark),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2.5),
            ("TOPPADDING", (0, 0), (-1, 0), 2.5),
            ("GRID", (0, 0), (-1, -1), 0.5, c_border),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("TOPPADDING", (0, 1), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(t_sweep)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()


# ─────────────────────────────────────────────
#  STREAMLIT APPLICATION MAIN
# ─────────────────────────────────────────────

def main():
    # Page configuration
    st.set_page_config(
        page_title="Microstrip Patch Antenna Design Studio v2.0",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling
    st.markdown("""
    <style>
        .stApp {
            background-color: #0b0f19;
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #090d16 100%);
            border-right: 1px solid #1e293b;
        }
        .result-card {
            background: linear-gradient(135deg, #131d33 0%, #1a2642 100%);
            border: 1px solid #233558;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .result-card:hover {
            border-color: #00e5ff;
            transform: translateY(-2px);
        }
        .result-card h4 {
            margin: 0 0 6px 0;
            font-size: 0.80rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .result-card .value {
            font-size: 1.55rem;
            font-weight: 700;
            color: #38bdf8;
        }
        .result-card .unit {
            font-size: 0.85rem;
            color: #67e8f9;
            margin-left: 5px;
        }
        .substrate-badge {
            background: linear-gradient(135deg, #0e1e38 0%, #172a4d 100%);
            border: 1px solid #0284c7;
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 10px;
            margin-bottom: 12px;
        }
        .substrate-badge h5 {
            margin: 0 0 4px 0;
            font-size: 0.88rem;
            color: #00e5ff;
        }
        .substrate-badge p {
            margin: 0;
            font-size: 0.78rem;
            color: #cbd5e1;
            line-height: 1.5;
        }
        .formula-box {
            background: #0d1424;
            border: 1px solid #1e293b;
            border-left: 4px solid #00e5ff;
            border-radius: 8px;
            padding: 16px 20px;
            margin: 12px 0;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 0.88rem;
            color: #e2e8f0;
            line-height: 1.9;
        }
        .info-banner {
            background: linear-gradient(135deg, #0e223d, #142d52);
            border: 1px solid #0284c7;
            border-radius: 10px;
            padding: 12px 18px;
            color: #bae6fd;
            font-size: 0.86rem;
            margin-top: 8px;
            margin-bottom: 14px;
            line-height: 1.5;
        }
        .warning-banner {
            background: linear-gradient(135deg, #2b1f11, #3b2816);
            border: 1px solid #d97706;
            border-radius: 10px;
            padding: 10px 14px;
            color: #fde68a;
            font-size: 0.80rem;
            margin-top: 6px;
            margin-bottom: 8px;
        }
        .section-title {
            font-size: 1.12rem;
            font-weight: 600;
            color: #f8fafc;
            border-bottom: 2px solid #1e293b;
            padding-bottom: 6px;
            margin: 22px 0 14px 0;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid #1e293b;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #131d33;
            border: 1px solid #1e293b;
            border-radius: 8px 8px 0px 0px;
            color: #94a3b8;
            padding: 8px 16px;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1e293b !important;
            border-bottom: 2px solid #00e5ff !important;
            color: #00e5ff !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Session State Initialization
    if "single_res" not in st.session_state:
        st.session_state["single_res"] = design_antenna(2.4, 4.4, 1.6)
    if "selected_mat_name" not in st.session_state:
        st.session_state["selected_mat_name"] = "FR4"
    if "sweep_df" not in st.session_state:
        st.session_state["sweep_df"] = None
    if "sweep_params" not in st.session_state:
        st.session_state["sweep_params"] = None

    # Sidebar: Substrate Material Selection & Target Inputs
    with st.sidebar:
        st.markdown("## 📡 Design Studio v2.0")
        st.markdown("---")

        st.markdown("### 🧩 Substrate Material Selection")
        mat_options = list(SUBSTRATE_DATABASE.keys())
        selected_mat_name = st.selectbox(
            "Select Substrate Material",
            options=mat_options,
            index=0,
            help="Select a standard microwave laminate or configure a custom dielectric material.",
        )
        st.session_state["selected_mat_name"] = selected_mat_name
        mat_preset = SUBSTRATE_DATABASE[selected_mat_name]

        if selected_mat_name == "Custom Material":
            eps_r_val = st.number_input(
                "Dielectric Constant (εᵣ) – Custom",
                min_value=1.0,
                max_value=100.0,
                value=float(mat_preset["eps_r"]),
                step=0.05,
                format="%.3f",
                help="Enter relative permittivity εᵣ for your custom substrate material (vacuum = 1.0).",
            )
        else:
            st.markdown(
                f"""
                <div style='background:#10192e; border:1px solid #1e293b; border-radius:6px; padding:6px 12px; margin-bottom:8px;'>
                    <span style='font-size:0.75rem; color:#94a3b8;'>Nominal Dielectric Constant (εᵣ):</span><br>
                    <b style='font-size:1.15rem; color:#00e5ff;'>{mat_preset['eps_r']:.2f}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
            eps_r_val = float(mat_preset["eps_r"])

        h_mm_val = st.number_input(
            "Substrate Thickness h (mm)",
            min_value=0.01,
            max_value=25.0,
            value=float(mat_preset["default_h_mm"]),
            step=0.1,
            format="%.3f",
            help="Physical substrate thickness in millimetres (mm).",
        )

        st.markdown(f"""
        <div class='substrate-badge'>
            <h5>{selected_mat_name}</h5>
            <p><b>Nominal εᵣ:</b> {eps_r_val:.3f} &nbsp;|&nbsp; <b>Loss Tan δ:</b> {mat_preset['loss_tangent']}</p>
            <p style='margin-top:4px;'>{mat_preset['description']}</p>
        </div>
        <div class='warning-banner'>
            ⚠️ <b>Datasheet Notice:</b> Material properties are nominal catalog values. Always verify dielectric constants and loss tangents using manufacturer datasheets for exact tolerances at your target frequency.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🎯 Single-Frequency Target")
        freq_ghz_val = st.number_input(
            "Operating Frequency (GHz)",
            min_value=0.1,
            max_value=100.0,
            value=2.40,
            step=0.1,
            format="%.2f",
            help="Resonant center frequency for the microstrip antenna in GHz.",
        )

        calculate_btn = st.button("⚡ Calculate Dimensions", use_container_width=True, type="primary")

        if calculate_btn:
            input_errors = validate_inputs(freq_ghz_val, eps_r_val, h_mm_val)
            if input_errors:
                for err in input_errors:
                    st.error(err)
            else:
                st.session_state["single_res"] = design_antenna(freq_ghz_val, eps_r_val, h_mm_val)
                st.success("Calculated patch dimensions successfully!")

    # Main application header
    st.markdown("""
    <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;'>
        <div>
            <h1 style='color:#00e5ff; margin-bottom:2px; font-size:2.1rem; letter-spacing:-0.02em;'>
                📡 Microstrip Patch Antenna Design Studio
            </h1>
            <p style='color:#94a3b8; font-size:0.95rem; margin-top:0;'>
                Version 2.0 • Transmission-Line Model Synthesis &amp; Parametric Frequency Sweep
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='info-banner'>
        ℹ️ <b>Welcome to Version 2.0:</b> Select from standard microwave substrates (FR4, Rogers RO4003C, Rogers RT/duroid 5880) or custom materials.
        Explore resonant patch synthesis in <b>Single-Frequency Design</b>, analyze broadband behavior in <b>Frequency Sweep Analysis</b>, and export an executive <b>PDF Design Report</b> with real charts and formulas.
    </div>
    """, unsafe_allow_html=True)

    # Tab navigation
    tab_single, tab_sweep, tab_pdf, tab_theory = st.tabs([
        "🎯 Single-Frequency Design",
        "📈 Frequency Sweep Analysis",
        "📄 PDF Design Report",
        "📚 Substrate Reference & Theory",
    ])

    # ── TAB 1 ──
    with tab_single:
        res = st.session_state["single_res"]
        current_mat = st.session_state["selected_mat_name"]

        st.markdown(f"### 📊 Design Results for **{current_mat}** at **{res['freq_ghz']:.3f} GHz**")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='result-card'>
                <h4>Patch Width (W)</h4>
                <span class='value'>{res['W_mm']:.3f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class='result-card'>
                <h4>Effective Permittivity (εeff)</h4>
                <span class='value'>{res['eps_eff']:.4f}</span>
                <span class='unit'>dimensionless</span>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class='result-card'>
                <h4>Physical Patch Length (L)</h4>
                <span class='value'>{res['L_mm']:.3f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class='result-card'>
                <h4>Effective Length (Leff)</h4>
                <span class='value'>{res['L_eff_mm']:.3f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class='result-card'>
                <h4>Fringing Extension (ΔL)</h4>
                <span class='value'>{res['dL_mm']:.4f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class='result-card'>
                <h4>Free-Space Wavelength (λ₀)</h4>
                <span class='value'>{res['lambda_mm']:.3f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🖼️ Antenna Geometry & Dimension Breakdown</div>", unsafe_allow_html=True)
        fig_col1, fig_col2 = st.columns(2)

        with fig_col1:
            fig_patch = draw_patch_diagram(res["W_mm"], res["L_mm"], res["h_mm"], for_report=False)
            st.pyplot(fig_patch, use_container_width=True)
            plt.close(fig_patch)

        with fig_col2:
            fig_bar = draw_comparison_chart(res["W_mm"], res["L_mm"], res["L_eff_mm"], res["dL_mm"], for_report=False)
            st.pyplot(fig_bar, use_container_width=True)
            plt.close(fig_bar)

        st.markdown("<div class='section-title'>📋 Synthesis Parameters Table</div>", unsafe_allow_html=True)
        summary_df = pd.DataFrame({
            "Parameter Description": [
                "Operating Resonant Frequency (f0)",
                "Substrate Material Name",
                "Relative Permittivity (εᵣ)",
                "Substrate Thickness (h)",
                "Patch Width (W)",
                "Effective Dielectric Constant (εeff)",
                "Fringing Length Extension (ΔL)",
                "Effective Resonant Length (Leff)",
                "Physical Patch Length (L)",
                "Free-Space Wavelength (λ₀)",
            ],
            "Value": [
                f"{res['freq_ghz']:.3f}",
                current_mat,
                f"{res['eps_r']:.3f}",
                f"{res['h_mm']:.3f}",
                f"{res['W_mm']:.4f}",
                f"{res['eps_eff']:.6f}",
                f"{res['dL_mm']:.4f}",
                f"{res['L_eff_mm']:.4f}",
                f"{res['L_mm']:.4f}",
                f"{res['lambda_mm']:.4f}",
            ],
            "Unit": ["GHz", "—", "—", "mm", "mm", "—", "mm", "mm", "mm", "mm"],
            "Classification": [
                "Input Target", "Material Selected", "Material Property (Nominal)", "Input Dimension",
                "Calculated Dimension", "Derived Field Parameter", "Calculated Extension",
                "Resonant Dimension", "Final Physical Dimension", "Fundamental Metric"
            ],
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        single_csv_bytes = generate_single_csv(res, current_mat)
        st.download_button(
            label="📥 Download Single Design as CSV",
            data=single_csv_bytes,
            file_name=f"microstrip_patch_{current_mat}_{res['freq_ghz']}GHz.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── TAB 2: FREQUENCY SWEEP ANALYSIS ──
    with tab_sweep:
        st.markdown("### 📈 Frequency Sweep Analysis")
        st.markdown(f"""
        Perform parametric frequency sweep analysis to evaluate how patch width and physical length scale across an operating band
        using the active substrate material (<b>{st.session_state['selected_mat_name']}</b>, nominal εᵣ = {res['eps_r']:.3f}, h = {res['h_mm']:.3f} mm).
        """, unsafe_allow_html=True)

        sw_col1, sw_col2, sw_col3 = st.columns(3)
        with sw_col1:
            sw_f_start = st.number_input(
                "Start Frequency (GHz)",
                min_value=0.1,
                max_value=100.0,
                value=1.50,
                step=0.1,
                format="%.2f",
                help="Lowest frequency for the sweep in GHz.",
            )
        with sw_col2:
            sw_f_stop = st.number_input(
                "Stop Frequency (GHz)",
                min_value=0.2,
                max_value=100.0,
                value=3.50,
                step=0.1,
                format="%.2f",
                help="Highest frequency for the sweep in GHz.",
            )
        with sw_col3:
            sw_f_step = st.number_input(
                "Frequency Step (GHz)",
                min_value=0.01,
                max_value=5.0,
                value=0.10,
                step=0.01,
                format="%.2f",
                help="Step increment between sweep calculation points.",
            )

        run_sweep_btn = st.button("🚀 Run Frequency Sweep", type="primary", use_container_width=True)

        if run_sweep_btn:
            sweep_errors = validate_sweep_inputs(sw_f_start, sw_f_stop, sw_f_step)
            if sweep_errors:
                for err in sweep_errors:
                    st.error(err)
            else:
                with st.spinner("Calculating parametric frequency sweep..."):
                    sweep_results_df = run_frequency_sweep(
                        sw_f_start, sw_f_stop, sw_f_step, res["eps_r"], res["h_mm"]
                    )
                    st.session_state["sweep_df"] = sweep_results_df
                    st.session_state["sweep_params"] = {
                        "start": sw_f_start,
                        "stop": sw_f_stop,
                        "step": sw_f_step,
                        "mat": st.session_state["selected_mat_name"],
                        "eps_r": res["eps_r"],
                        "h_mm": res["h_mm"],
                    }
                    st.success(f"Sweep computed successfully with {len(sweep_results_df)} frequency points!")

        if st.session_state["sweep_df"] is not None:
            sweep_df = st.session_state["sweep_df"]
            params = st.session_state["sweep_params"]

            st.markdown("<div class='section-title'>📊 Sweep Overview & Key Extremes</div>", unsafe_allow_html=True)
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.metric("Total Sweep Points", f"{len(sweep_df)}")
            with m_col2:
                st.metric("Min Width (W)", f"{sweep_df['Patch Width W (mm)'].min():.2f} mm")
            with m_col3:
                st.metric("Max Width (W)", f"{sweep_df['Patch Width W (mm)'].max():.2f} mm")
            with m_col4:
                st.metric("Min Length (L)", f"{sweep_df['Physical Length L (mm)'].min():.2f} mm")
            with m_col5:
                st.metric("Max Length (L)", f"{sweep_df['Physical Length L (mm)'].max():.2f} mm")

            st.markdown("<div class='section-title'>📈 Parametric Sweep Curves</div>", unsafe_allow_html=True)
            g_col1, g_col2 = st.columns(2)

            with g_col1:
                fig_w = draw_frequency_vs_width_plot(sweep_df, for_report=False)
                st.pyplot(fig_w, use_container_width=True)
                plt.close(fig_w)

            with g_col2:
                fig_l = draw_frequency_vs_length_plot(sweep_df, for_report=False)
                st.pyplot(fig_l, use_container_width=True)
                plt.close(fig_l)

            st.markdown("<div class='section-title'>📋 Parametric Sweep Results Table</div>", unsafe_allow_html=True)
            st.dataframe(sweep_df, use_container_width=True, hide_index=True)

            sweep_csv_bytes = generate_sweep_csv(
                sweep_df,
                params["mat"],
                params["eps_r"],
                params["h_mm"],
            )
            st.download_button(
                label="📥 Download Frequency Sweep Results as CSV",
                data=sweep_csv_bytes,
                file_name=f"frequency_sweep_{params['start']}-{params['stop']}GHz_{params['mat']}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("👆 Configure the frequency range above and click **🚀 Run Frequency Sweep** to analyze dimensions across the band.")

    # ── TAB 3: PDF DESIGN REPORT ──
    with tab_pdf:
        st.markdown("### 📄 Executive PDF Design Report")
        st.markdown("""
        Generate an executive, publication-grade engineering PDF report containing your verified calculations,
        material properties, design formulas, design summary, and actual generated diagrams.
        """)

        r_res = st.session_state["single_res"]
        r_mat = st.session_state["selected_mat_name"]
        r_sweep = st.session_state.get("sweep_df", None)

        col_rep_info, col_rep_action = st.columns([2, 1])

        with col_rep_info:
            st.markdown(f"""
            <div style='background:#10192e; border:1px solid #1e293b; border-radius:10px; padding:16px 20px;'>
                <h4 style='color:#00e5ff; margin-top:0;'>Report Content Inclusion</h4>
                <ul style='color:#cbd5e1; font-size:0.88rem; line-height:1.7;'>
                    <li><b>Project Title:</b> Microstrip Patch Antenna Design Studio – Version 2.0</li>
                    <li><b>Selected Substrate:</b> {r_mat} (Nominal εᵣ = {r_res['eps_r']:.3f}, h = {r_res['h_mm']:.3f} mm)</li>
                    <li><b>Target Frequency:</b> {r_res['freq_ghz']:.3f} GHz (λ₀ = {r_res['lambda_mm']:.2f} mm)</li>
                    <li><b>Calculated Dimensions:</b> W = {r_res['W_mm']:.3f} mm, L = {r_res['L_mm']:.3f} mm, Leff = {r_res['L_eff_mm']:.3f} mm, ΔL = {r_res['dL_mm']:.4f} mm</li>
                    <li><b>Formulas:</b> Complete transmission-line model equations with Balanis &amp; Bahl-Trivedi citations</li>
                    <li><b>Diagrams:</b> Actual top-view patch geometry and dimension comparison bar chart</li>
                    <li><b>Frequency Sweep Status:</b> {'Included (' + str(len(r_sweep)) + ' points & graphs)' if r_sweep is not None else 'Not executed (run in Tab 2 to include)'}</li>
                    <li><b>Technical Summary:</b> Physical resonant behavior, fringing effect, and 50 Ω feed considerations</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_rep_action:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_pdf_btn = st.button("🔨 Generate / Refresh PDF Report", type="primary", use_container_width=True)

        if generate_pdf_btn or ("cached_pdf_bytes" not in st.session_state):
            with st.spinner("Rendering publication-grade PDF report..."):
                fig_p_rep = draw_patch_diagram(r_res["W_mm"], r_res["L_mm"], r_res["h_mm"], for_report=True)
                patch_png = fig_to_png_bytes(fig_p_rep)
                plt.close(fig_p_rep)

                fig_b_rep = draw_comparison_chart(r_res["W_mm"], r_res["L_mm"], r_res["L_eff_mm"], r_res["dL_mm"], for_report=True)
                bar_png = fig_to_png_bytes(fig_b_rep)
                plt.close(fig_b_rep)

                sw_w_png = None
                sw_l_png = None
                if r_sweep is not None and not r_sweep.empty:
                    fig_sw_w = draw_frequency_vs_width_plot(r_sweep, for_report=True)
                    sw_w_png = fig_to_png_bytes(fig_sw_w)
                    plt.close(fig_sw_w)

                    fig_sw_l = draw_frequency_vs_length_plot(r_sweep, for_report=True)
                    sw_l_png = fig_to_png_bytes(fig_sw_l)
                    plt.close(fig_sw_l)

                pdf_report_bytes = build_pdf_report(
                    single_res=r_res,
                    material_info={"name": r_mat, "eps_r": r_res["eps_r"], "h_mm": r_res["h_mm"]},
                    sweep_df=r_sweep,
                    patch_img_bytes=patch_png,
                    bar_img_bytes=bar_png,
                    sweep_w_bytes=sw_w_png,
                    sweep_l_bytes=sw_l_png,
                )
                st.session_state["cached_pdf_bytes"] = pdf_report_bytes

        if "cached_pdf_bytes" in st.session_state:
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Download PDF Design Report",
                data=st.session_state["cached_pdf_bytes"],
                file_name=f"Microstrip_Patch_Design_Report_{r_mat}_{r_res['freq_ghz']}GHz.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("✅ PDF Design Report ready for download! Generated from actual inputs and calculations.")

    # ── TAB 4: SUBSTRATE REFERENCE & THEORY ──
    with tab_theory:
        st.markdown("### 📚 Substrate Reference & Mathematical Theory")

        st.markdown("<div class='section-title'>📋 Microwave Substrate Reference Table</div>", unsafe_allow_html=True)
        mat_summary_df = pd.DataFrame({
            "Material Name": [
                "FR4 (Glass Epoxy)",
                "Rogers RO4003C",
                "Rogers RT/duroid 5880",
                "Alumina (96%)",
                "PTFE (Teflon)",
            ],
            "Nominal εᵣ": [4.40, 3.55, 2.20, 9.80, 2.10],
            "Typical Loss Tan (tan δ)": ["0.0200", "0.0027", "0.0009", "0.0002", "0.0004"],
            "Typical Thickness h (mm)": [1.60, 0.813, 0.787, 0.635, "0.50 – 3.20"],
            "Recommended Application": [
                "Low-cost prototypes, sub-6 GHz, education",
                "Commercial RF, cellular base stations, automotive radar",
                "High-frequency microwave, Ku-band, aerospace, minimum loss",
                "Thin-film hybrid circuits, millimeter-wave",
                "Stripline and low-loss microstrip filters",
            ],
        })
        st.dataframe(mat_summary_df, use_container_width=True, hide_index=True)

        st.markdown("<div class='section-title'>📐 Governing Equations (Transmission-Line Model)</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='formula-box'>
        <b>1. Radiating Patch Width (W):</b><br>
        &nbsp;&nbsp;&nbsp;W = c / (2·f₀) · √(2 / (εᵣ + 1))<br>
        &nbsp;&nbsp;&nbsp;<i>Chosen to provide efficient radiation while avoiding higher-order transverse modes.</i><br><br>

        <b>2. Effective Dielectric Constant (εeff):</b><br>
        &nbsp;&nbsp;&nbsp;εeff = (εᵣ + 1)/2 + (εᵣ − 1)/2 · (1 + 12·h/W)^(−½)<br>
        &nbsp;&nbsp;&nbsp;<i>Accounts for fringing electromagnetic fields partially traveling in air (εᵣ=1) and substrate.</i><br><br>

        <b>3. Fringing Length Extension (ΔL):</b><br>
        &nbsp;&nbsp;&nbsp;ΔL = 0.412 · h · [(εeff + 0.3)(W/h + 0.264)] / [(εeff − 0.258)(W/h + 0.8)]<br>
        &nbsp;&nbsp;&nbsp;<i>Represents the apparent electrical extension at each open-circuited radiating edge (Hammerstad equation).</i><br><br>

        <b>4. Effective Resonant Patch Length (Leff):</b><br>
        &nbsp;&nbsp;&nbsp;Leff = c / (2·f₀·√εeff)<br>
        &nbsp;&nbsp;&nbsp;<i>The fundamental half-wavelength resonant condition in the effective dielectric medium.</i><br><br>

        <b>5. Synthesized Physical Length (L):</b><br>
        &nbsp;&nbsp;&nbsp;L = Leff − 2·ΔL<br>
        &nbsp;&nbsp;&nbsp;<i>Physical metallization length obtained by subtracting fringe extensions from both edges.</i><br><br>

        <small style='color:#64748b;'>
        References: Bahl &amp; Trivedi, "A Designer's Guide to Microstrip Line", Microwaves (1977);
        C. A. Balanis, "Antenna Theory: Analysis and Design", 3rd Edition, John Wiley &amp; Sons.
        </small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>⚙️ Practical Engineering Considerations</div>", unsafe_allow_html=True)
        st.markdown("""
        - **Substrate Thickness (h):** Thick substrates increase operational impedance bandwidth and radiation efficiency, but excessively thick substrates ($h > 0.05\\lambda_0$) excite unwanted surface waves that degrade the radiation pattern and reduce gain.
        - **Dielectric Permittivity (εᵣ):** Low permittivity (e.g., Rogers RT/duroid 5880 with $\\varepsilon_r \\approx 2.2$) yields larger physical patches with wider bandwidth and higher efficiency. High permittivity substrates (e.g., Alumina or FR4) produce compact, miniaturized patches with narrower bandwidth.
        - **Impedance Matching:** The radiation resistance at the edge of a half-wavelength rectangular patch typically ranges from $150\\ \\Omega$ to $300\\ \\Omega$. Common feeding techniques to match to $50\\ \\Omega$ coaxial systems include **inset-fed microstrip notches** and **coaxial probe feeding** placed at $y_0 = \\frac{L}{\\pi} \\arccos\\left(\\sqrt{\\frac{50}{R_{in}}}\\right)$.
        - **Theoretical Disclaimer:** Transmission-line models assume planar TEM/quasi-TEM wave propagation with magnetic wall boundaries. Fabricated antennas must be verified using full-wave 3D electromagnetic simulators (ANSYS HFSS, CST Studio Suite, openEMS) to account for finite ground planes, surface waves, feed discontinuities, and substrate tolerances.
        """)

    st.markdown("<br><hr style='border-color:#1e293b;'><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; color:#64748b; font-size:0.80rem; line-height:1.6;'>
        <b>Microstrip Patch Antenna Design Studio – Version 2.0</b><br>
        Engineered with Python, Streamlit, NumPy, Pandas, Matplotlib &amp; ReportLab.<br>
        Theoretical transmission-line model synthesis. Always verify with manufacturer datasheets &amp; EM simulation.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
