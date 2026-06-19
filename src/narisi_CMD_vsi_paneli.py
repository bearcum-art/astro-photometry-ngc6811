import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import math

# ============================================================
# Skupna obdelava B-V CMD za več panelov
# ============================================================

base = Path(
    r"C:\Users\jakal\Desktop\2.letnik\Astronomija 1\Astro_projekt\Meritve_obdelava"
)

fot_dir = base / "Fotometrija"

# Seznam parov: ime_rezultata, mapa, V datoteka, B datoteka
pairs = [
    {
        "name": "P01",
        "folder": fot_dir / "P01",
        "v_file": "P01_V_psf.lst",
        "b_file": "P01_B_psf.lst",
    },
    {
        "name": "P02",
        "folder": fot_dir / "P02",
        "v_file": "P02_V_psf.lst",
        "b_file": "P02_B_psf.lst",
    },
    {
        "name": "P04_P05",
        "folder": fot_dir / "P04_P05",
        "v_file": "P04_V_psf.lst",
        "b_file": "P05_B_psf.lst",
    },
    {
        "name": "P05_P06",
        "folder": fot_dir / "P05_P06",
        "v_file": "P05_V_psf.lst",
        "b_file": "P06_B_psf.lst",
    },
    {
        "name": "P06_P07",
        "folder": fot_dir / "P06_P07",
        "v_file": "P06_V_psf.lst",
        "b_file": "P07_B_psf.lst",
    },
]

max_dist_pix = 5.0

# ============================================================
# Funkcije
# ============================================================

def read_psf(path):
    """Prebere Siril Dynamic PSF .lst datoteko."""
    df = pd.read_csv(path, decimal=",")

    numeric_cols = ["x0", "y0", "Ra", "Dec", "FWHMx", "FWHMy", "Mag", "r", "RMSE"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["x0", "y0", "Mag", "r"])
    return df


def match_stars(v_df, b_df, max_dist=5.0):
    """Poveže zvezde med V in B seznamom po najbližjih x0/y0 koordinatah."""
    matches = []

    # Za naše število zvezd je ta enostaven način dovolj hiter.
    for _, vstar in v_df.iterrows():
        vx = vstar["x0"]
        vy = vstar["y0"]

        dx = b_df["x0"] - vx
        dy = b_df["y0"] - vy
        dist = (dx * dx + dy * dy) ** 0.5

        best_idx = dist.idxmin()
        best_dist = dist.loc[best_idx]

        if best_dist <= max_dist:
            bstar = b_df.loc[best_idx]

            v_mag = vstar["Mag"]
            b_mag = bstar["Mag"]
            b_minus_v = b_mag - v_mag

            matches.append({
                "x_V": vstar["x0"],
                "y_V": vstar["y0"],
                "RA_V": vstar.get("Ra", math.nan),
                "Dec_V": vstar.get("Dec", math.nan),
                "V_mag": v_mag,
                "B_mag": b_mag,
                "B_minus_V": b_minus_v,
                "dist_pix": best_dist,
                "FWHM_V": vstar.get("FWHMx", math.nan),
                "FWHM_B": bstar.get("FWHMx", math.nan),
                "r_V": vstar["r"],
                "r_B": bstar["r"],
            })

    return pd.DataFrame(matches)


def make_cmd_plot(df, name, out_dir):
    """Nariše očiščen instrumentalni CMD."""
    out_dir.mkdir(exist_ok=True)

    out_png = out_dir / f"{name}_CMD_instrumental_clean_v1.png"
    out_pdf = out_dir / f"{name}_CMD_instrumental_clean_v1.pdf"

    # Mehko čiščenje
    df_plot = df[
        (df["dist_pix"] <= 5.0) &
        (df["r_V"] >= 0.7) &
        (df["r_B"] >= 0.7)
    ].copy()

    if len(df_plot) > 20:
        x_low, x_high = df_plot["B_minus_V"].quantile([0.005, 0.995])
        y_low, y_high = df_plot["V_mag"].quantile([0.005, 0.995])

        df_plot = df_plot[
            (df_plot["B_minus_V"] >= x_low) &
            (df_plot["B_minus_V"] <= x_high) &
            (df_plot["V_mag"] >= y_low) &
            (df_plot["V_mag"] <= y_high)
        ].copy()

    plt.figure(figsize=(9, 6))
    plt.scatter(df_plot["B_minus_V"], df_plot["V_mag"], s=9, alpha=0.65)

    plt.xlabel("Instrumentalni barvni indeks B - V")
    plt.ylabel("Instrumentalna magnituda V")
    plt.title(f"CMD za {name} - očiščeni instrumentalni podatki")

    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.25)
    plt.tight_layout(pad=1.5)

    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()

    return len(df_plot), out_png, out_pdf


# ============================================================
# Glavni program
# ============================================================

summary = []

for pair in pairs:
    name = pair["name"]
    folder = pair["folder"]
    v_path = folder / pair["v_file"]
    b_path = folder / pair["b_file"]

    print()
    print("=" * 60)
    print(f"Obdelujem: {name}")
    print(f"V: {v_path}")
    print(f"B: {b_path}")

    if not v_path.exists():
        print(f"MANJKA V datoteka: {v_path}")
        continue

    if not b_path.exists():
        print(f"MANJKA B datoteka: {b_path}")
        continue

    v_df = read_psf(v_path)
    b_df = read_psf(b_path)

    matched = match_stars(v_df, b_df, max_dist=max_dist_pix)

    matched_csv = folder / f"{name}_BV_matched.csv"
    clean_csv = folder / f"{name}_BV_clean.csv"
    plot_csv = folder / f"{name}_CMD_plot.csv"

    matched.to_csv(matched_csv, index=False, decimal=",")

    # Clean CSV za nadaljnje delo
    clean = matched[
        (matched["dist_pix"] <= 5.0) &
        (matched["r_V"] >= 0.7) &
        (matched["r_B"] >= 0.7)
    ].copy()

    clean.to_csv(clean_csv, index=False, decimal=",")

    # Poseben CSV samo za CMD graf
    clean[["B_minus_V", "V_mag"]].to_csv(plot_csv, index=False, decimal=",")

    graph_dir = folder / "Grafi"
    n_plot, out_png, out_pdf = make_cmd_plot(clean, name, graph_dir)

    print(f"V zvezd: {len(v_df)}")
    print(f"B zvezd: {len(b_df)}")
    print(f"Ujemanih zvezd: {len(matched)}")
    print(f"Točk na grafu: {n_plot}")
    print(f"Shranjeno: {out_png}")
    print(f"Shranjeno: {out_pdf}")

    summary.append({
        "panel": name,
        "V_stars": len(v_df),
        "B_stars": len(b_df),
        "matched": len(matched),
        "plotted": n_plot,
    })

# Povzetek
summary_df = pd.DataFrame(summary)
summary_path = fot_dir / "BV_CMD_povzetek_panelov.csv"
summary_df.to_csv(summary_path, index=False, decimal=",")

print()
print("=" * 60)
print("POVZETEK")
print(summary_df)
print()
print(f"Povzetek shranjen v: {summary_path}")