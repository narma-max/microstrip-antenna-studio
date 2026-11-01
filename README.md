# 📡 Microstrip Patch Antenna Design Studio – Version 2.0

A professional, engineering-grade **Streamlit web application** for synthesizing, analyzing, and reporting rectangular microstrip patch antennas using the standard **Transmission-Line Model** equations.

---

## 🌟 What's New in Version 2.0

| Feature | Description |
|---|---|
| 🧩 **Substrate Material Selection** | Choose from industry-standard microwave laminates (**FR4**, **Rogers RO4003C**, **Rogers RT/duroid 5880**) or define a **Custom Material** with auto-populating nominal dielectric constants ($\varepsilon_r$) and thickness presets. |
| 📈 **Frequency Sweep Analysis** | Parametric sweep over user-defined frequency bands ($f_{start}$ to $f_{stop}$ with configurable step). Calculates $W$, $\varepsilon_{eff}$, $\Delta L$, $L_{eff}$, and $L$ across the band with clean tabular views and CSV export. |
| 📊 **Dual Parametric Graphs** | Auto-generates **Frequency vs. Patch Width** and **Frequency vs. Physical Patch Length** curves with high-contrast styling. |
| 📄 **Executive PDF Design Report** | One-click download of a publication-grade engineering PDF report containing actual inputs, calculated dimensions, mathematical formulas, design summary, and high-resolution diagrams. |
| 🎨 **Refined Navy/Cyan Theme** | Modern, responsive dark UI styled with deep navy blue (`#0b0f19`), crisp white text, and vivid cyan (`#00e5ff`) accents organized into intuitive tabs. |
| 🛡️ **Robust Input Validation** | Comprehensive boundary checks preventing division-by-zero, non-positive dimensions, or invalid frequency ranges. |

---

## 📐 Design Equations (Transmission-Line Model)

All calculations follow the established transmission-line formulation (Bahl & Trivedi, 1977; C. A. Balanis, *Antenna Theory: Analysis and Design*):

1. **Patch Width ($W$):**
   $$W = \frac{c}{2 f_0} \sqrt{\frac{2}{\varepsilon_r + 1}}$$
   *Optimized for radiation efficiency while suppressing higher-order modes.*

2. **Effective Dielectric Constant ($\varepsilon_{eff}$):**
   $$\varepsilon_{eff} = \frac{\varepsilon_r + 1}{2} + \frac{\varepsilon_r - 1}{2}\left(1 + 12\frac{h}{W}\right)^{-1/2}$$
   *Accounts for fringing electromagnetic fields propagating in both substrate and surrounding air.*

3. **Fringing Length Extension ($\Delta L$):**
   $$\Delta L = 0.412 h \frac{(\varepsilon_{eff} + 0.3)\left(\frac{W}{h} + 0.264\right)}{(\varepsilon_{eff} - 0.258)\left(\frac{W}{h} + 0.8\right)}$$
   *Apparent electrical extension at each open radiating edge (Hammerstad relation).*

4. **Effective Patch Length ($L_{eff}$):**
   $$L_{eff} = \frac{c}{2 f_0 \sqrt{\varepsilon_{eff}}}$$
   *Resonant electrical half-wavelength condition.*

5. **Physical Patch Length ($L$):**
   $$L = L_{eff} - 2\Delta L$$
   *Physical copper dimension after compensating for fringing at both non-radiating edges.*

---

## 🧪 Benchmark Verification Example

| Parameter | Symbol | Value | Units |
|---|---|---|---|
| Design Frequency | $f_0$ | **2.400** | GHz |
| Substrate | — | **FR4** | — |
| Relative Permittivity | $\varepsilon_r$ | **4.400** | — (Nominal) |
| Substrate Thickness | $h$ | **1.600** | mm |
| **Synthesized Patch Width** | $W$ | **38.036** | mm |
| **Effective Dielectric Constant** | $\varepsilon_{eff}$ | **4.0858** | — |
| **Fringing Length Extension** | $\Delta L$ | **0.7388** | mm |
| **Effective Patch Length** | $L_{eff}$ | **30.920** | mm |
| **Physical Patch Length** | $L$ | **29.442** | mm |
| Free-Space Wavelength | $\lambda_0$ | **125.000** | mm |

---

## 📦 Supported Substrate Materials

| Substrate Material | Nominal $\varepsilon_r$ | Loss Tangent ($\tan \delta$) | Typical Thickness $h$ | Key Applications |
|---|---|---|---|---|
| **FR4 (Glass Epoxy)** | 4.40 | 0.0200 | 1.60 mm | Cost-effective prototyping, sub-6 GHz, educational labs |
| **Rogers RO4003C** | 3.55 | 0.0027 | 0.813 mm | Commercial RF, 5G base stations, low loss microstrip |
| **Rogers RT/duroid 5880**| 2.20 | 0.0009 | 0.787 mm | Aerospace, radar, satellite comms, Ku-band, minimum loss |
| **Custom Material** | User-defined | User-defined | User-defined | Specialized dielectric substrates, novel ceramics, flexible films |

> ⚠️ **Manufacturer Datasheet Notice:** Material properties in the application are nominal catalog values. Always verify dielectric constants and loss tangents with manufacturer datasheets at your specific operating frequency and temperature.

---

## 🚀 Installation & Setup

### 1. Open the project folder

```powershell
cd "c:\microstrip patch antenna"
```

### 2. Activate the virtual environment

```powershell
# Windows
.\venv\Scripts\Activate.ps1
# or
venv\Scripts\activate.bat
```

### 3. Install or update dependencies

```powershell
pip install -r requirements.txt
```

---

## 💻 Running the Application

Launch the Streamlit web application using:

```powershell
python -m streamlit run app.py
```

The application will start and open in your default browser at:
👉 **http://localhost:8501**

---

## 📑 Project Structure

```
microstrip patch antenna/
├── app.py                     ← Complete Streamlit Application (Version 2.0)
├── requirements.txt           ← Project dependencies (including reportlab)
├── README.md                  ← Documentation, theory, and operational manual
├── test_app_v2.py             ← Comprehensive automated unit test suite (8 tests)
├── backup_v1/                 ← Preserved Version 1.0 original backup files
│   ├── app_v1_backup.py
│   ├── requirements_v1_backup.txt
│   └── README_v1_backup.md
└── venv/                      ← Python 3.9 virtual environment
```

---

## ⚙️ Engineering Disclaimer

All dimensions generated by this studio are based on the **analytic Transmission-Line Model**. While highly accurate for initial geometry synthesis, physical antennas require full-wave 3D electromagnetic validation (ANSYS HFSS, CST Studio Suite, openEMS) and physical impedance tuning (e.g., inset feed depth, coaxial probe placement) to account for:
- Finite ground plane truncation
- Feed line discontinuities and connector parasitics
- Surface wave propagation on thick substrates ($h > 0.05 \lambda_0$)
- Dielectric tolerance variations and manufacturing etching limits
