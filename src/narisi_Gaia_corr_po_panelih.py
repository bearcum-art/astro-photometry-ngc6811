import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

base = Path(
    r"C:\Users\jakal\Desktop\2.letnik\Astronomija 1\Astro_projekt\Meritve_obdelava"
)

in_csv = base / "Fotometrija" / "Skupni_CMD_Gaia_corr" / "skupni_CMD_Gaia_corr_plot.csv"
out_dir = base / "Fotometrija" / "Skupni_CMD_Gaia_corr"

out_png = out_dir / "skupni_CMD_Gaia_corr_po_panelih_v1.png"
out_pdf = out_dir / "skupni_CMD_Gaia_corr_po_panelih_v1.pdf"

df = pd.read_csv(in_csv, decimal=",")

for col in ["B_minus_V_gaia_approx", "V_gaia_approx"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["panel", "B_minus_V_gaia_approx", "V_gaia_approx"])

print("Točke po panelih:")
print(df["panel"].value_counts())

plt.figure(figsize=(10, 6))

for panel, group in df.groupby("panel"):
    plt.scatter(
        group["B_minus_V_gaia_approx"],
        group["V_gaia_approx"],
        s=6,
        alpha=0.45,
        label=panel,
    )

plt.xlabel("Približno poravnan barvni indeks: B−V ~ Gaia BP−RP")
plt.ylabel("Približna magnituda: V ~ Gaia G")
plt.title("Skupni CMD po panelih - Gaia/corr približna poravnava")

plt.gca().invert_yaxis()
plt.grid(True, alpha=0.25)
plt.legend(markerscale=2, fontsize=9)
plt.tight_layout(pad=1.5)

plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")

plt.show()

print(f"Shranjeno PNG: {out_png}")
print(f"Shranjeno PDF: {out_pdf}")