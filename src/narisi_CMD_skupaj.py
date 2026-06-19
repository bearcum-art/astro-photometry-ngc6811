import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# Skupni B-V CMD iz vseh uporabnih panelov
# ============================================================

base = Path(
    r"C:\Users\jakal\Desktop\2.letnik\Astronomija 1\Astro_projekt\Meritve_obdelava"
)

fot_dir = base / "Fotometrija"
out_dir = fot_dir / "Skupni_CMD"
out_dir.mkdir(exist_ok=True)

# Paneli, ki jih združimo
panels = [
    {
        "name": "P01",
        "csv": fot_dir / "P01" / "P01_BV_clean.csv",
    },
    {
        "name": "P02",
        "csv": fot_dir / "P02" / "P02_BV_clean.csv",
    },
    {
        "name": "P04_P05",
        "csv": fot_dir / "P04_P05" / "P04_P05_BV_clean.csv",
    },
    {
        "name": "P05_P06",
        "csv": fot_dir / "P05_P06" / "P05_P06_BV_clean.csv",
    },
    {
        "name": "P06_P07",
        "csv": fot_dir / "P06_P07" / "P06_P07_BV_clean.csv",
    },
]

# ============================================================
# Branje in združevanje podatkov
# ============================================================

all_data = []

for panel in panels:
    name = panel["name"]
    csv_path = panel["csv"]

    if not csv_path.exists():
        print(f"Manjka datoteka: {csv_path}")
        continue

    df = pd.read_csv(csv_path, decimal=",")
    df["panel"] = name

    all_data.append(df)

if not all_data:
    raise RuntimeError("Ni bilo najdenih vhodnih datotek.")

df_all = pd.concat(all_data, ignore_index=True)

# Pretvorba potrebnih stolpcev v številke
cols = ["B_minus_V", "V_mag", "dist_pix", "r_V", "r_B"]

for col in cols:
    df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

df_all = df_all.dropna(subset=cols)

# ============================================================
# Mehko čiščenje
# ============================================================

df_plot = df_all[
    (df_all["dist_pix"] <= 5.0) &
    (df_all["r_V"] >= 0.7) &
    (df_all["r_B"] >= 0.7)
].copy()

# Odstranimo najbolj ekstremne osamelce
x_low, x_high = df_plot["B_minus_V"].quantile([0.005, 0.995])
y_low, y_high = df_plot["V_mag"].quantile([0.005, 0.995])

df_plot = df_plot[
    (df_plot["B_minus_V"] >= x_low) &
    (df_plot["B_minus_V"] <= x_high) &
    (df_plot["V_mag"] >= y_low) &
    (df_plot["V_mag"] <= y_high)
].copy()

# ============================================================
# Shranjevanje združenih podatkov
# ============================================================

combined_csv = out_dir / "skupni_CMD_podatki.csv"
plot_csv = out_dir / "skupni_CMD_plot.csv"

df_all.to_csv(combined_csv, index=False, decimal=",")
df_plot[["panel", "B_minus_V", "V_mag"]].to_csv(plot_csv, index=False, decimal=",")

# ============================================================
# Izpis povzetka
# ============================================================

print("Skupni CMD")
print("----------")
print(f"Vseh združenih točk: {len(df_all)}")
print(f"Točk na grafu po čiščenju: {len(df_plot)}")
print()

print("Število točk po panelih:")
print(df_plot["panel"].value_counts())
print()

print("Statistika grafa:")
print(df_plot[["B_minus_V", "V_mag"]].describe())

# ============================================================
# Risanje skupnega CMD
# ============================================================

out_png = out_dir / "skupni_CMD_instrumental_clean_v1.png"
out_pdf = out_dir / "skupni_CMD_instrumental_clean_v1.pdf"

plt.figure(figsize=(9, 6))

plt.scatter(
    df_plot["B_minus_V"],
    df_plot["V_mag"],
    s=6,
    alpha=0.45
)

plt.xlabel("Instrumentalni barvni indeks B - V")
plt.ylabel("Instrumentalna magnituda V")
plt.title("Skupni CMD - očiščeni instrumentalni podatki")

plt.gca().invert_yaxis()
plt.grid(True, alpha=0.25)
plt.tight_layout(pad=1.5)

plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")

plt.show()

print()
print(f"Shranjeno PNG: {out_png}")
print(f"Shranjeno PDF: {out_pdf}")
print(f"Združeni podatki: {combined_csv}")
print(f"Podatki za graf: {plot_csv}")