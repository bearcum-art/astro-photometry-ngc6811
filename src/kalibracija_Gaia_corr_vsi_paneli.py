import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from astropy.io import fits

# ============================================================
# Gaia/corr približna kalibracija za vse uporabne panele
# ============================================================

base = Path(
    r"C:\Users\jakal\Desktop\2.letnik\Astronomija 1\Astro_projekt\Meritve_obdelava"
)

fot_dir = base / "Fotometrija"
out_dir = fot_dir / "Skupni_CMD_Gaia_corr"
out_dir.mkdir(exist_ok=True)

NAXIS2 = 2664

panels = [
    {
        "name": "P01",
        "pair": "P01_V + P01_B",
        "csv": fot_dir / "P01" / "P01_BV_clean.csv",
        "corr": fot_dir / "P01" / "Astrometry" / "P01_V_astrometry_corr.fits",
    },
    {
        "name": "P02",
        "pair": "P02_V + P02_B",
        "csv": fot_dir / "P02" / "P02_BV_clean.csv",
        "corr": fot_dir / "P02" / "Astrometry" / "P02_V_astrometry_corr.fits",
    },
    {
        "name": "P04_P05",
        "pair": "P04_V + P05_B",
        "csv": fot_dir / "P04_P05" / "P04_P05_BV_clean.csv",
        "corr": fot_dir / "P04_P05" / "Astrometry" / "P04_V_astrometry_corr.fits",
    },
    {
        "name": "P05_P06",
        "pair": "P05_V + P06_B",
        "csv": fot_dir / "P05_P06" / "P05_P06_BV_clean.csv",
        "corr": fot_dir / "P05_P06" / "Astrometry" / "P05_V_astrometry_corr.fits",
    },
    {
        "name": "P06_P07",
        "pair": "P06_V + P07_B",
        "csv": fot_dir / "P06_P07" / "P06_P07_BV_clean.csv",
        "corr": fot_dir / "P06_P07" / "Astrometry" / "P06_V_astrometry_corr.fits",
    },
]


def read_siril(csv_path):
    siril = pd.read_csv(csv_path, decimal=",")

    needed_cols = [
        "x_V",
        "y_V",
        "V_mag",
        "B_mag",
        "B_minus_V",
        "dist_pix",
        "r_V",
        "r_B",
    ]

    for col in needed_cols:
        siril[col] = pd.to_numeric(siril[col], errors="coerce")

    siril = siril.dropna(subset=needed_cols)

    siril = siril[
        (siril["dist_pix"] <= 5.0) &
        (siril["r_V"] >= 0.7) &
        (siril["r_B"] >= 0.7)
    ].copy()

    siril["x_ast"] = siril["x_V"]
    siril["y_ast"] = NAXIS2 - siril["y_V"]

    return siril


def read_corr(corr_path):
    with fits.open(corr_path) as hdul:
        data = hdul[1].data

        corr = pd.DataFrame({
            "field_x": data["field_x"],
            "field_y": data["field_y"],
            "field_ra": data["field_ra"],
            "field_dec": data["field_dec"],
            "index_ra": data["index_ra"],
            "index_dec": data["index_dec"],
            "mag": data["mag"],
            "phot_bp_mean_mag": data["phot_bp_mean_mag"],
            "phot_rp_mean_mag": data["phot_rp_mean_mag"],
        })

    for col in corr.columns:
        corr[col] = pd.to_numeric(corr[col], errors="coerce")

    corr = corr.dropna(subset=[
        "field_x",
        "field_y",
        "mag",
        "phot_bp_mean_mag",
        "phot_rp_mean_mag",
    ]).copy()

    corr["BP_minus_RP"] = corr["phot_bp_mean_mag"] - corr["phot_rp_mean_mag"]

    return corr


def match_siril_to_corr(siril, corr, max_pix_sep=5.0):
    matches = []

    corr_x = corr["field_x"].values
    corr_y = corr["field_y"].values

    for _, row in siril.iterrows():
        sx = row["x_ast"]
        sy = row["y_ast"]

        dx = corr_x - sx
        dy = corr_y - sy
        dist = np.sqrt(dx * dx + dy * dy)

        j = np.argmin(dist)
        best_dist = dist[j]

        if best_dist <= max_pix_sep:
            c = corr.iloc[j]

            matches.append({
                "x_V": row["x_V"],
                "y_V": row["y_V"],
                "x_ast": sx,
                "y_ast": sy,
                "pixel_sep": best_dist,

                "B_inst": row["B_mag"],
                "V_inst": row["V_mag"],
                "B_minus_V_inst": row["B_minus_V"],

                "field_ra": c["field_ra"],
                "field_dec": c["field_dec"],

                "G_Gaia": c["mag"],
                "BP_Gaia": c["phot_bp_mean_mag"],
                "RP_Gaia": c["phot_rp_mean_mag"],
                "BP_minus_RP_Gaia": c["BP_minus_RP"],
            })

    return pd.DataFrame(matches)


all_calibrated = []
summary_rows = []

for item in panels:
    name = item["name"]
    pair = item["pair"]
    csv_path = item["csv"]
    corr_path = item["corr"]

    print()
    print("=" * 70)
    print(f"Obdelujem {name}: {pair}")

    if not csv_path.exists():
        print(f"MANJKA CSV: {csv_path}")
        continue

    if not corr_path.exists():
        print(f"MANJKA CORR: {corr_path}")
        continue

    siril = read_siril(csv_path)
    corr = read_corr(corr_path)

    m = match_siril_to_corr(siril, corr, max_pix_sep=5.0)

    print(f"Siril zvezd po filtru: {len(siril)}")
    print(f"Astrometry/Gaia corr zvezd: {len(corr)}")
    print(f"Ujemanj Siril ↔ corr.fits znotraj 5 px: {len(m)}")

    if len(m) < 10:
        print("PREMALO UJEMANJ. Panel preskočen.")
        continue

    m["ZP_V_to_G"] = m["G_Gaia"] - m["V_inst"]
    m["offset_color_to_BPRP"] = m["BP_minus_RP_Gaia"] - m["B_minus_V_inst"]

    ZP_V_raw = m["ZP_V_to_G"].median()
    color_offset_raw = m["offset_color_to_BPRP"].median()

    m_cal = m[
        (np.abs(m["ZP_V_to_G"] - ZP_V_raw) < 2.0) &
        (np.abs(m["offset_color_to_BPRP"] - color_offset_raw) < 2.0)
    ].copy()

    ZP_V_to_G = m_cal["ZP_V_to_G"].median()
    color_offset = m_cal["offset_color_to_BPRP"].median()

    std_V = m_cal["ZP_V_to_G"].std()
    std_color = m_cal["offset_color_to_BPRP"].std()

    print(f"Kalibracijskih ujemanj: {len(m_cal)}")
    print(f"V_inst -> G_Gaia offset = {ZP_V_to_G:.4f} mag")
    print(f"(B-V)_inst -> (BP-RP)_Gaia offset = {color_offset:.4f} mag")
    print(f"std V offset = {std_V:.4f} mag")
    print(f"std color offset = {std_color:.4f} mag")

    # Shrani individualna ujemanja
    panel_out_dir = fot_dir / name / "Gaia_corr_kalibracija"
    panel_out_dir.mkdir(exist_ok=True)

    m.to_csv(panel_out_dir / f"{name}_Gaia_corr_matched.csv", index=False, decimal=",")

    # Uporabi offsete na cel panel
    siril["panel"] = name
    siril["pair"] = pair
    siril["V_gaia_approx"] = siril["V_mag"] + ZP_V_to_G
    siril["B_minus_V_gaia_approx"] = siril["B_minus_V"] + color_offset

    all_calibrated.append(siril)

    summary_rows.append({
        "panel": name,
        "pair": pair,
        "siril_stars": len(siril),
        "corr_stars": len(corr),
        "matched_corr": len(m),
        "calibration_matches": len(m_cal),
        "V_offset_to_G": ZP_V_to_G,
        "color_offset_to_BPRP": color_offset,
        "std_V_offset": std_V,
        "std_color_offset": std_color,
    })

# ============================================================
# Skupni izhod
# ============================================================

summary = pd.DataFrame(summary_rows)
summary_csv = out_dir / "Gaia_corr_povzetek_panelov.csv"
summary.to_csv(summary_csv, index=False, decimal=",")

print()
print("=" * 70)
print("POVZETEK OFFSETOV")
print(summary)

if not all_calibrated:
    raise RuntimeError("Noben panel ni bil uspešno kalibriran.")

df_all = pd.concat(all_calibrated, ignore_index=True)

combined_csv = out_dir / "skupni_CMD_Gaia_corr_podatki.csv"
df_all.to_csv(combined_csv, index=False, decimal=",")

# Grafična selekcija
df_plot = df_all.copy()

x_low, x_high = df_plot["B_minus_V_gaia_approx"].quantile([0.005, 0.995])
y_low, y_high = df_plot["V_gaia_approx"].quantile([0.005, 0.995])

df_plot = df_plot[
    (df_plot["B_minus_V_gaia_approx"] >= x_low) &
    (df_plot["B_minus_V_gaia_approx"] <= x_high) &
    (df_plot["V_gaia_approx"] >= y_low) &
    (df_plot["V_gaia_approx"] <= y_high)
].copy()

plot_csv = out_dir / "skupni_CMD_Gaia_corr_plot.csv"
df_plot[["panel", "B_minus_V_gaia_approx", "V_gaia_approx"]].to_csv(
    plot_csv,
    index=False,
    decimal=",",
)

# ============================================================
# Skupni graf
# ============================================================

out_png = out_dir / "skupni_CMD_Gaia_corr_v1.png"
out_pdf = out_dir / "skupni_CMD_Gaia_corr_v1.pdf"

plt.figure(figsize=(10, 6))

plt.scatter(
    df_plot["B_minus_V_gaia_approx"],
    df_plot["V_gaia_approx"],
    s=5,
    alpha=0.35,
)

plt.xlabel("Približno poravnan barvni indeks: B−V ~ Gaia BP−RP")
plt.ylabel("Približna magnituda: V ~ Gaia G")
plt.title("Skupni CMD - približno poravnan z Gaia prek corr.fits")

plt.gca().invert_yaxis()
plt.grid(True, alpha=0.25)
plt.tight_layout(pad=1.5)

plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")
plt.show()

# ============================================================
# Graf po panelih
# ============================================================

out_panel_png = out_dir / "skupni_CMD_Gaia_corr_po_panelih_v1.png"
out_panel_pdf = out_dir / "skupni_CMD_Gaia_corr_po_panelih_v1.pdf"

plt.figure(figsize=(10, 6))

for panel_name, group in df_plot.groupby("panel"):
    plt.scatter(
        group["B_minus_V_gaia_approx"],
        group["V_gaia_approx"],
        s=6,
        alpha=0.45,
        label=panel_name,
    )

plt.xlabel("Približno poravnan barvni indeks: B−V ~ Gaia BP−RP")
plt.ylabel("Približna magnituda: V ~ Gaia G")
plt.title("Skupni CMD po panelih - Gaia/corr približna poravnava")

plt.gca().invert_yaxis()
plt.grid(True, alpha=0.25)
plt.legend(markerscale=2, fontsize=9)
plt.tight_layout(pad=1.5)

plt.savefig(out_panel_png, dpi=300, bbox_inches="tight")
plt.savefig(out_panel_pdf, bbox_inches="tight")
plt.show()

print()
print("Shranjeno:")
print(f"Povzetek: {summary_csv}")
print(f"Skupni podatki: {combined_csv}")
print(f"Plot podatki: {plot_csv}")
print(f"Skupni CMD PNG: {out_png}")
print(f"Skupni CMD PDF: {out_pdf}")
print(f"Skupni CMD po panelih PNG: {out_panel_png}")
print(f"Skupni CMD po panelih PDF: {out_panel_pdf}")