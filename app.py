"""
Microstrip Patch Antenna Design Studio
---------------------------------------
Calculates rectangular microstrip patch antenna dimensions using
standard transmission-line model equations.

Author : Antenna Design Studio
Version: 1.0.0
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import io
import csv

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Microstrip Patch Antenna Design Studio",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d2e 0%, #16192a 100%);
        border-right: 1px solid #2d3154;
    }

    /* Cards */
    .result-card {
        background: linear-gradient(135deg, #1e2235 0%, #252840 100%);
        border: 1px solid #3d4270;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .result-card h4 {
        margin: 0 0 6px 0;
        font-size: 0.82rem;
        color: #8b9ab8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .result-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #7eb8f7;
    }
    .result-card .unit {
        font-size: 0.9rem;
        color: #5a7ab0;
        margin-left: 4px;
    }

    /* Formula box */
    .formula-box {
        background: #12151f;
        border: 1px solid #2d3154;
        border-left: 4px solid #4f6ef7;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
        font-size: 0.88rem;
        color: #c5d0e8;
        line-height: 1.9;
    }

    /* Warning banner */
    .info-banner {
        background: linear-gradient(135deg, #1c2540, #1e2a45);
        border: 1px solid #3a5080;
        border-radius: 10px;
        padding: 12px 18px;
        color: #90afd4;
        font-size: 0.85rem;
        margin-top: 8px;
    }

    /* Section headers */
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #c5d0f0;
        border-bottom: 1px solid #2d3154;
        padding-bottom: 6px;
        margin: 20px 0 14px 0;
    }

    /* Error box */
    .error-box {
        background: #2a1520;
        border: 1px solid #8b2a3a;
        border-radius: 10px;
        padding: 14px 18px;
        color: #f08090;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  ANTENNA DESIGN EQUATIONS
# ─────────────────────────────────────────────

def speed_of_light() -> float:
    """Returns speed of light in m/s."""
    return 3e8


def calc_patch_width(freq_hz: float, eps_r: float) -> float:
    """
    Patch Width (W)  [metres]
    W = c / (2 * f) * sqrt(2 / (eps_r + 1))
    """
    c = speed_of_light()
    return (c / (2 * freq_hz)) * np.sqrt(2 / (eps_r + 1))


def calc_effective_dielectric(eps_r: float, h: float, W: float) -> float:
    """
    Effective dielectric constant (eps_eff)
    eps_eff = (eps_r+1)/2 + (eps_r-1)/2 * (1 + 12*h/W)^(-0.5)
    Valid when W/h > 1.
    """
    return (eps_r + 1) / 2 + (eps_r - 1) / 2 * (1 + 12 * h / W) ** (-0.5)


def calc_delta_L(eps_eff: float, h: float, W: float) -> float:
    """
    Fringing length extension (ΔL)  [metres]
    ΔL = 0.412 * h * (eps_eff + 0.3) * (W/h + 0.264)
                    / ((eps_eff - 0.258) * (W/h + 0.8))
    """
    ratio = W / h
    numerator   = (eps_eff + 0.3) * (ratio + 0.264)
    denominator = (eps_eff - 0.258) * (ratio + 0.8)
    return 0.412 * h * (numerator / denominator)


def calc_effective_length(freq_hz: float, eps_eff: float) -> float:
    """
    Effective patch length (L_eff)  [metres]
    L_eff = c / (2 * f * sqrt(eps_eff))
    """
    c = speed_of_light()
    return c / (2 * freq_hz * np.sqrt(eps_eff))


def calc_physical_length(L_eff: float, delta_L: float) -> float:
    """
    Physical patch length (L)  [metres]
    L = L_eff - 2 * ΔL
    """
    return L_eff - 2 * delta_L


def design_antenna(freq_ghz: float, eps_r: float, h_mm: float) -> dict:
    """
    Run full antenna design and return a dict with all parameters in mm.
    """
    freq_hz = freq_ghz * 1e9
    h_m     = h_mm * 1e-3                          # substrate thickness in m

    W       = calc_patch_width(freq_hz, eps_r)
    eps_eff = calc_effective_dielectric(eps_r, h_m, W)
    dL      = calc_delta_L(eps_eff, h_m, W)
    L_eff   = calc_effective_length(freq_hz, eps_eff)
    L       = calc_physical_length(L_eff, dL)

    return {
        "freq_ghz"  : freq_ghz,
        "eps_r"     : eps_r,
        "h_mm"      : h_mm,
        "W_mm"      : W    * 1e3,
        "eps_eff"   : eps_eff,
        "dL_mm"     : dL   * 1e3,
        "L_eff_mm"  : L_eff * 1e3,
        "L_mm"      : L    * 1e3,
    }


# ─────────────────────────────────────────────
#  VALIDATION
# ─────────────────────────────────────────────

def validate_inputs(freq_ghz, eps_r, h_mm):
    errors = []

    if freq_ghz <= 0:
        errors.append("❌ Frequency must be a positive number greater than 0 GHz.")
    if freq_ghz > 100:
        errors.append("❌ Frequency above 100 GHz is outside the typical microstrip design range.")

    if eps_r < 1:
        errors.append("❌ Relative permittivity (εᵣ) must be ≥ 1 (vacuum = 1).")
    if eps_r > 100:
        errors.append("❌ Relative permittivity (εᵣ) seems unrealistically high (max typical: ~100).")

    if h_mm <= 0:
        errors.append("❌ Substrate thickness must be a positive value in mm.")
    if h_mm > 20:
        errors.append("❌ Substrate thickness > 20 mm is unusually large for microstrip antennas.")

    return errors


# ─────────────────────────────────────────────
#  MATPLOTLIB FIGURES
# ─────────────────────────────────────────────

def draw_patch_diagram(W_mm: float, L_mm: float, h_mm: float) -> plt.Figure:
    """
    Draw a top-view rectangular patch diagram with dimension annotations.
    """
    fig, ax = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#12151f")

    pad_x = W_mm * 0.35
    pad_y = L_mm * 0.40

    # Ground plane backdrop
    gp = mpatches.FancyBboxPatch(
        (-pad_x, -pad_y), W_mm + 2 * pad_x, L_mm + 2 * pad_y,
        boxstyle="round,pad=0", linewidth=1.5,
        edgecolor="#3d5080", facecolor="#1a2035"
    )
    ax.add_patch(gp)

    # Substrate layer hint (hatching)
    sub = mpatches.FancyBboxPatch(
        (-pad_x * 0.6, -pad_y * 0.6),
        W_mm + 1.2 * pad_x, L_mm + 1.2 * pad_y,
        boxstyle="round,pad=0", linewidth=0,
        facecolor="#1d2540", alpha=0.6
    )
    ax.add_patch(sub)

    # Radiating patch (gold/copper colour)
    patch_rect = mpatches.FancyBboxPatch(
        (0, 0), W_mm, L_mm,
        boxstyle="round,pad=0.5",
        linewidth=2, edgecolor="#f0c040",
        facecolor="#c8961a", alpha=0.90
    )
    ax.add_patch(patch_rect)

    # Feed point dot
    ax.plot(W_mm / 2, L_mm * 0.15, 'o', color="#ff6060", markersize=8, zorder=5)
    ax.text(W_mm / 2 + W_mm * 0.06, L_mm * 0.13, "Feed point",
            color="#ff9090", fontsize=8, va="center")

    # ── Width annotation (horizontal) ──
    arrow_y = -pad_y * 0.45
    ax.annotate(
        "", xy=(W_mm, arrow_y), xytext=(0, arrow_y),
        arrowprops=dict(arrowstyle="<->", color="#7eb8f7", lw=1.5)
    )
    ax.text(W_mm / 2, arrow_y - pad_y * 0.18,
            f"W = {W_mm:.2f} mm", ha="center", va="top",
            color="#7eb8f7", fontsize=10, fontweight="bold")

    # ── Length annotation (vertical) ──
    arrow_x = W_mm + pad_x * 0.45
    ax.annotate(
        "", xy=(arrow_x, L_mm), xytext=(arrow_x, 0),
        arrowprops=dict(arrowstyle="<->", color="#80e8a0", lw=1.5)
    )
    ax.text(arrow_x + pad_x * 0.18, L_mm / 2,
            f"L = {L_mm:.2f} mm", ha="left", va="center",
            color="#80e8a0", fontsize=10, fontweight="bold",
            rotation=90)

    # ── Substrate label ──
    ax.text(-pad_x * 0.55, -pad_y * 0.55,
            f"Substrate  εᵣ = {h_mm:.2f} mm",
            color="#8090b0", fontsize=7.5, va="top")

    ax.set_xlim(-pad_x, W_mm + pad_x * 1.5)
    ax.set_ylim(-pad_y * 1.2, L_mm + pad_y)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Patch Antenna — Top View", color="#c5d0f0",
                 fontsize=13, fontweight="bold", pad=14)

    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3154")

    fig.tight_layout()
    return fig


def draw_comparison_chart(W_mm: float, L_mm: float,
                           L_eff_mm: float, dL_mm: float) -> plt.Figure:
    """
    Bar chart comparing W, L, L_eff, and ΔL.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#12151f")

    labels  = ["Width (W)", "Physical Length (L)", "Effective Length (Leff)", "Fringe Ext. (ΔL)"]
    values  = [W_mm, L_mm, L_eff_mm, dL_mm]
    colors  = ["#4f8ef7", "#80e8a0", "#f7c948", "#f07878"]

    bars = ax.barh(labels, values, color=colors, edgecolor="#2d3154",
                   height=0.5, linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(val + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"  {val:.3f} mm", va="center", color="#c5d0f0", fontsize=9)

    ax.set_xlabel("Dimension (mm)", color="#8b9ab8", fontsize=10)
    ax.set_title("Patch Dimension Comparison", color="#c5d0f0",
                 fontsize=13, fontweight="bold")
    ax.tick_params(colors="#8b9ab8")
    ax.xaxis.label.set_color("#8b9ab8")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3154")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, max(values) * 1.22)
    ax.grid(axis="x", color="#2d3154", linestyle="--", alpha=0.5)

    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────
#  CSV EXPORT
# ─────────────────────────────────────────────

def generate_csv(results: dict) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Parameter", "Value", "Unit"])
    writer.writerow(["Target Frequency",        results["freq_ghz"],  "GHz"])
    writer.writerow(["Substrate εᵣ",            results["eps_r"],     "—"])
    writer.writerow(["Substrate Thickness (h)", results["h_mm"],      "mm"])
    writer.writerow(["Patch Width (W)",          f'{results["W_mm"]:.4f}',    "mm"])
    writer.writerow(["Effective Dielectric (εeff)", f'{results["eps_eff"]:.6f}', "—"])
    writer.writerow(["Fringe Length Ext. (ΔL)", f'{results["dL_mm"]:.4f}',   "mm"])
    writer.writerow(["Effective Length (Leff)", f'{results["L_eff_mm"]:.4f}', "mm"])
    writer.writerow(["Physical Patch Length (L)", f'{results["L_mm"]:.4f}',  "mm"])
    writer.writerow([])
    writer.writerow(["Note", "All results are theoretical estimates based on the transmission-line model."])
    return output.getvalue().encode("utf-8")


# ─────────────────────────────────────────────
#  SIDEBAR — INPUTS
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📡 Design Parameters")
    st.markdown("---")

    freq_ghz = st.number_input(
        "Target Frequency (GHz)",
        min_value=0.1, max_value=100.0,
        value=2.4, step=0.1, format="%.2f",
        help="Operating frequency of the antenna in GHz."
    )

    eps_r = st.number_input(
        "Substrate Relative Permittivity (εᵣ)",
        min_value=1.0, max_value=100.0,
        value=4.4, step=0.1, format="%.2f",
        help="Dielectric constant of the substrate material. FR4 ≈ 4.4, Rogers RT/duroid 5880 ≈ 2.2."
    )

    h_mm = st.number_input(
        "Substrate Thickness h (mm)",
        min_value=0.01, max_value=20.0,
        value=1.6, step=0.1, format="%.2f",
        help="Physical thickness of the substrate in millimetres."
    )

    st.markdown("---")
    calculate_btn = st.button("⚡ Calculate", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; color:#5a6a8a; line-height:1.7;'>
    <b>Common Substrates</b><br>
    • FR4          &nbsp;&nbsp;&nbsp;&nbsp; εᵣ ≈ 4.4, h = 1.6 mm<br>
    • RT/duroid 5880 εᵣ ≈ 2.2, h = 0.79 mm<br>
    • Rogers 4003  &nbsp; εᵣ ≈ 3.55, h = 0.813 mm<br>
    • Alumina      &nbsp;&nbsp;&nbsp;&nbsp; εᵣ ≈ 9.8, h = 0.635 mm
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────

st.markdown("""
<h1 style='text-align:center; color:#7eb8f7; margin-bottom:2px;'>
    📡 Microstrip Patch Antenna Design Studio
</h1>
<p style='text-align:center; color:#5a7ab0; font-size:0.95rem; margin-bottom:24px;'>
    Rectangular patch design using the Transmission-Line Model
</p>
""", unsafe_allow_html=True)

# ── Info banner ──
st.markdown("""
<div class='info-banner'>
    ℹ️  <b>How to use:</b> Enter your antenna parameters in the left sidebar and click <b>⚡ Calculate</b>.
    All results are <em>theoretical estimates</em> based on the standard transmission-line model
    and should be fine-tuned with EM simulation software (e.g., CST, HFSS, or openEMS).
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────

if calculate_btn:
    errors = validate_inputs(freq_ghz, eps_r, h_mm)

    if errors:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='error-box'>" +
            "<b>Please fix the following input error(s):</b><br>" +
            "<br>".join(errors) +
            "</div>",
            unsafe_allow_html=True
        )
    else:
        res = design_antenna(freq_ghz, eps_r, h_mm)

        # ── Result Cards ──
        st.markdown("<div class='section-title'>📊 Calculated Results</div>", unsafe_allow_html=True)

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
                <h4>Effective Dielectric Constant (εeff)</h4>
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
                <h4>Effective Length (L_eff)</h4>
                <span class='value'>{res['L_eff_mm']:.3f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class='result-card'>
                <h4>Fringing Length Extension (ΔL)</h4>
                <span class='value'>{res['dL_mm']:.4f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

            lambda_mm = (3e8 / (freq_ghz * 1e9)) * 1e3
            st.markdown(f"""
            <div class='result-card'>
                <h4>Free-Space Wavelength (λ₀)</h4>
                <span class='value'>{lambda_mm:.3f}</span>
                <span class='unit'>mm</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Diagrams ──
        st.markdown("<div class='section-title'>🖼️ Antenna Diagram & Comparison</div>",
                    unsafe_allow_html=True)

        fig_col1, fig_col2 = st.columns(2)
        with fig_col1:
            fig_patch = draw_patch_diagram(res["W_mm"], res["L_mm"], h_mm)
            st.pyplot(fig_patch, use_container_width=True)
            plt.close(fig_patch)

        with fig_col2:
            fig_bar = draw_comparison_chart(
                res["W_mm"], res["L_mm"], res["L_eff_mm"], res["dL_mm"]
            )
            st.pyplot(fig_bar, use_container_width=True)
            plt.close(fig_bar)

        # ── Design Equations ──
        st.markdown("<div class='section-title'>📐 Design Equations Used</div>",
                    unsafe_allow_html=True)

        st.markdown("""
        <div class='formula-box'>
        <b>1. Patch Width (W)</b><br>
        &nbsp;&nbsp;&nbsp;W = c / (2·f) · √(2 / (εᵣ + 1))<br><br>

        <b>2. Effective Dielectric Constant (εeff)</b><br>
        &nbsp;&nbsp;&nbsp;εeff = (εᵣ+1)/2 + (εᵣ−1)/2 · (1 + 12·h/W)^(−½)<br><br>

        <b>3. Fringing Length Extension (ΔL)</b><br>
        &nbsp;&nbsp;&nbsp;ΔL = 0.412 · h · [(εeff + 0.3)(W/h + 0.264)] / [(εeff − 0.258)(W/h + 0.8)]<br><br>

        <b>4. Effective Patch Length (Leff)</b><br>
        &nbsp;&nbsp;&nbsp;Leff = c / (2·f·√εeff)<br><br>

        <b>5. Physical Patch Length (L)</b><br>
        &nbsp;&nbsp;&nbsp;L = Leff − 2·ΔL<br><br>

        <small style='color:#4a5a7a;'>
        Reference: Bahl &amp; Trivedi (1977) / C. A. Balanis "Antenna Theory: Analysis and Design"
        </small>
        </div>
        """, unsafe_allow_html=True)

        # ── Summary Table ──
        st.markdown("<div class='section-title'>📋 Full Results Summary</div>",
                    unsafe_allow_html=True)

        import pandas as pd
        df = pd.DataFrame({
            "Parameter": [
                "Target Frequency",
                "Substrate εᵣ",
                "Substrate Thickness (h)",
                "Patch Width (W)",
                "Effective Dielectric Constant (εeff)",
                "Fringing Length Extension (ΔL)",
                "Effective Patch Length (Leff)",
                "Physical Patch Length (L)",
                "Free-Space Wavelength (λ₀)",
            ],
            "Value": [
                f"{res['freq_ghz']:.3f}",
                f"{res['eps_r']:.3f}",
                f"{res['h_mm']:.3f}",
                f"{res['W_mm']:.4f}",
                f"{res['eps_eff']:.6f}",
                f"{res['dL_mm']:.4f}",
                f"{res['L_eff_mm']:.4f}",
                f"{res['L_mm']:.4f}",
                f"{lambda_mm:.4f}",
            ],
            "Unit": [
                "GHz", "—", "mm", "mm", "—", "mm", "mm", "mm", "mm"
            ],
            "Note": [
                "Input", "Input", "Input",
                "Calculated", "Calculated", "Calculated",
                "Calculated", "Calculated", "Derived",
            ]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── CSV Download ──
        csv_bytes = generate_csv(res)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_bytes,
            file_name=f"patch_antenna_{freq_ghz}GHz.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.markdown("""
        <div class='info-banner' style='margin-top:16px;'>
            ⚠️ <b>Disclaimer:</b> These results are <em>theoretical estimates</em> based on the
            transmission-line model. Fabricated antennas require EM simulation (CST/HFSS/openEMS)
            and physical tuning to account for manufacturing tolerances, connector effects,
            and surface-wave losses.
        </div>
        """, unsafe_allow_html=True)

else:
    # ── Welcome / placeholder ──
    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("""
        <div style='text-align:center; padding:50px 30px; background:#12151f;
                    border:1px dashed #2d3154; border-radius:16px;'>
            <div style='font-size:3.5rem;'>📡</div>
            <h3 style='color:#7eb8f7; margin:12px 0 8px;'>Ready to Design</h3>
            <p style='color:#5a7ab0; font-size:0.9rem; line-height:1.7;'>
                Enter your substrate and frequency parameters<br>
                in the sidebar, then click <b>⚡ Calculate</b><br>
                to see the full antenna design results.
            </p>
            <br>
            <p style='color:#3d4d6a; font-size:0.8rem;'>
                Default: 2.4 GHz · FR4 (εᵣ = 4.4) · h = 1.6 mm
            </p>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<hr style='border-color:#2d3154;'>
<p style='text-align:center; color:#3d4d6a; font-size:0.78rem;'>
    Microstrip Patch Antenna Design Studio · Transmission-Line Model ·
    Built with Python, Streamlit &amp; Matplotlib
</p>
""", unsafe_allow_html=True)
