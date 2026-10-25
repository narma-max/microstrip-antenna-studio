# 📡 Microstrip Patch Antenna Design Studio

A professional, beginner-friendly **Streamlit web app** that designs rectangular microstrip patch antennas using the standard **Transmission-Line Model** equations.

---

## Features

| Feature | Details |
|---|---|
| 🎯 Design Inputs | Frequency (GHz), Substrate εᵣ, Substrate thickness h (mm) |
| 📐 Calculations | Patch Width, Effective εᵣ, ΔL, Effective Length, Physical Length |
| 🖼️ Visualisations | Top-view patch diagram + bar comparison chart |
| 📋 Formula Reference | All equations shown with citations |
| 📥 CSV Export | One-click download of all results |
| ✅ Input Validation | Clear error messages for invalid inputs |

---

## Installation

### 1. Clone / open the project folder

```bash
# If you've just downloaded the files, navigate to the folder:
cd "microstrip patch antenna"
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

The app will open automatically at **http://localhost:8501** in your default browser.

---

## Usage

1. Use the **left sidebar** to enter:
   - Target frequency in GHz (e.g., `2.4` for Wi-Fi)
   - Substrate relative permittivity εᵣ (e.g., `4.4` for FR4)
   - Substrate thickness h in mm (e.g., `1.6` for standard FR4)
2. Click **⚡ Calculate**
3. View results, diagrams, and formula reference
4. Download results as CSV using the **📥 Download** button

---

## Design Equations (Transmission-Line Model)

| # | Equation | Description |
|---|---|---|
| 1 | `W = c / (2f) · √(2 / (εᵣ+1))` | Patch Width |
| 2 | `εeff = (εᵣ+1)/2 + (εᵣ-1)/2 · (1+12h/W)^(-½)` | Effective Dielectric Constant |
| 3 | `ΔL = 0.412h · (εeff+0.3)(W/h+0.264) / ((εeff-0.258)(W/h+0.8))` | Fringing Length Extension |
| 4 | `Leff = c / (2f√εeff)` | Effective Patch Length |
| 5 | `L = Leff - 2ΔL` | Physical Patch Length |

> **References:** Bahl & Trivedi (1977); C. A. Balanis, *Antenna Theory: Analysis and Design*, 3rd ed.

---

## Common Substrate Reference

| Material | εᵣ | Typical h (mm) |
|---|---|---|
| FR4 | 4.4 | 1.6 |
| Rogers RT/duroid 5880 | 2.2 | 0.79 |
| Rogers 4003C | 3.55 | 0.813 |
| Alumina (96%) | 9.8 | 0.635 |
| PTFE | 2.1 | 0.5–3.0 |

---

## Disclaimer

> All results are **theoretical estimates** based on the transmission-line model. Real antennas require electromagnetic simulation (CST Microwave Studio, ANSYS HFSS, or openEMS) and physical tuning for:
> - Manufacturing tolerances
> - Connector and feed effects
> - Surface-wave losses
> - Mutual coupling

---

## Tech Stack

- **Python 3.8+**
- **Streamlit** — interactive UI
- **NumPy** — numerical calculations
- **Matplotlib** — diagrams and charts
- **Pandas** — results table

---

## Project Structure

```
microstrip patch antenna/
├── app.py            ← Main Streamlit application
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```
