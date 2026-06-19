import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# Skupni CMD z instrumentalno poravnavo panelov
# ============================================================

base = Path(
    r"C:\Users\jakal\Desktop\2.letnik\Astronomija 1\Astro_projekt\Meritve_obdelava"
)

csv_path = base / "Fotometrija" / "Skupni_CMD" / "skupni_CMD_podatki.csv"
out_dir = base / "Fotometrija" / "Skupni_CMD"
out_dir.mkdir(exist_ok=True)

out_png = out_dir / "skupni_CMD_panelno_poravnan_v1.png"
out_pdf = out_dir / "skupni_CMD_panelno_poravnan_v1.pdf"
out_csv = out_dir / "skupni_CMD_panelno_poravnani_podatki.csv"
out_offsets = out_dir / "panelni_BV_odmiki.csv"

# ============================================================
# Branje podatkov
# ============================================================

df = pd.read_csv(csv_path, decimal=",")

cols = ["B_minus_V", "V_mag", "dist_pix", "r_V", "r_B"]

for col in cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=cols + ["panel"])

# Mehko čiščenje
df_plot = df[
    (df["dist_pix"] <= 5.0) &
    (df["r_V"] >= 0.7) &
    (df["r_B"] >= 0.7)
].copy()

# Odstranimo ekstremne osamelce pred izračunom median
x_low, x_high = df_plot["B_minus_V"].quantile([0.005, 0.995])
y_low, y_high = df_plot["V_mag"].quantile([0.005, 0.995])

df_plot = df_plot[
    (df_plot["B_minus_V"] >= x_low) &
    (df_plot["B_minus_V"] <= x_high) &
    (df_plot["V_mag"] >= y_low) &
    (df_plot["V_mag"] <= y_high)
].copy()

# ============================================================
# Poravnava panelov po mediani B-V
# ============================================================

panel_medians = df_plot.groupby("panel")["B_minus_V"].median()

# Referenca: skupna mediana vseh panelov
target_median = df_plot["B_minus_V"].median()

offsets = target_median - panel_medians

df_plot["BV_offset"] = df_plot["panel"].map(offsets)
df_plot["B_minus_V_aligned"] = df_plot["B_minus_V"] + df_plot["BV_offset"]

# Shranimo podatke in odmike
df_plot.to_csv(out_csv, index=False, decimal=",")

offset_table = pd.DataFrame({
    "panel": panel_medians.index,
    "median_B_minus_V_before": panel_medians.values,
    "target_median": target_median,
    "applied_offset": offsets.values,
})

offset_table.to_csv(out_offsets, index=False, decimal=",")

# ============================================================
# Izpis
# ============================================================

print("Panelna poravnava B-V")
print("---------------------")
print(f"Točk pred/po čiščenju za graf: {len(df_plot)}")
print(f"Ciljna skupna mediana B-V: {target_median:.4f}")
print()
print(offset_table)
print()

print("Mediane po poravnavi:")
print(df_plot.groupby("panel")[["B_minus_V_aligned", "V_mag"]].median())

# ============================================================
# Graf
# ============================================================

plt.figure(figsize=(10, 6))

plt.scatter(
    df_plot["B_minus_V_aligned"],
    df_plot["V_mag"],
    s=6,
    alpha=0.45
)

plt.xlabel("Panelno poravnan instrumentalni barvni indeks B - V")
plt.ylabel("Instrumentalna magnituda V")
plt.title("Skupni CMD - panelno poravnani instrumentalni podatki")

plt.gca().invert_yaxis()
plt.grid(True, alpha=0.25)
plt.tight_layout(pad=1.5)

plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")

plt.show()

print()
print(f"Shranjeno PNG: {out_png}")
print(f"Shranjeno PDF: {out_pdf}")
print(f"Poravnani podatki: {out_csv}")
print(f"Panelni odmiki: {out_offsets}")