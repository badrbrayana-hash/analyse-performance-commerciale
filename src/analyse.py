"""
Analyse de la performance commerciale - jeu de données Superstore Sales.

Lit data/raw/superstore_sales.csv, prépare les données, calcule les KPI,
produit les analyses (dont les ventes à perte) et exporte les graphiques
dans outputs/figures/.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
FIG = os.path.join(RACINE, "outputs", "figures")
os.makedirs(FIG, exist_ok=True)

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.bbox"] = "tight"

# 1. Chargement (encodage latin-1 : le fichier contient des accents)
brut = pd.read_csv(os.path.join(RACINE, "data", "raw", "superstore_sales.csv"),
                   encoding="latin-1")
print("Dimensions brutes :", brut.shape)

# 2. Préparation : sélection et renommage des colonnes utiles en français
colonnes = {
    "Order ID": "id_commande",
    "Order Date": "date_commande",
    "Product Name": "produit",
    "Product Category": "categorie",
    "Product Sub-Category": "sous_categorie",
    "Region": "region",
    "Province": "province",
    "Order Quantity": "quantite",
    "Sales": "chiffre_affaires",
    "Profit": "marge",
    "Discount": "remise",
    "Unit Price": "prix_unitaire",
    "Customer Segment": "segment_client",
    "Ship Mode": "mode_livraison",
}
df = brut[list(colonnes.keys())].rename(columns=colonnes).copy()
df["date_commande"] = pd.to_datetime(df["date_commande"], format="%m/%d/%Y")

print("Valeurs manquantes :", int(df.isna().sum().sum()))

df["taux_marge"] = df["marge"] / df["chiffre_affaires"]
df["mois"] = df["date_commande"].dt.to_period("M").dt.to_timestamp()
df["annee"] = df["date_commande"].dt.year
df["vente_a_perte"] = df["marge"] < 0

# 3. KPI globaux
ca_total = df["chiffre_affaires"].sum()
marge_totale = df["marge"].sum()
taux_marge_global = marge_totale / ca_total
nb_lignes = len(df)
nb_commandes = df["id_commande"].nunique()
panier_moyen = ca_total / nb_commandes
part_perte = df["vente_a_perte"].mean()

print("\n--- KPI globaux ---")
print(f"Chiffre d'affaires total   : {ca_total:>14,.0f}")
print(f"Marge (profit) totale      : {marge_totale:>14,.0f}")
print(f"Taux de marge global       : {taux_marge_global:>14.1%}")
print(f"Lignes de commande         : {nb_lignes:>14,}")
print(f"Commandes distinctes       : {nb_commandes:>14,}")
print(f"Panier moyen par commande  : {panier_moyen:>14,.0f}")
print(f"Part de lignes à perte     : {part_perte:>14.1%}")
print(f"Période                    : {df['date_commande'].min().date()} -> {df['date_commande'].max().date()}")

# 4. Évolution temporelle
ca_mensuel = df.groupby("mois")["chiffre_affaires"].sum()
plt.figure(figsize=(11, 4.5))
plt.plot(ca_mensuel.index, ca_mensuel.values, marker="o", linewidth=1.8, markersize=4)
plt.title("Évolution du chiffre d'affaires mensuel", fontsize=13, fontweight="bold")
plt.ylabel("CA")
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
plt.tight_layout()
plt.savefig(os.path.join(FIG, "01_ca_mensuel.png"))
plt.close()

# 5. Pareto par sous-catégorie
ca_sc = df.groupby("sous_categorie")["chiffre_affaires"].sum().sort_values(ascending=False)
ca_cum = ca_sc.cumsum() / ca_sc.sum()
n_80 = int((ca_cum <= 0.80).sum()) + 1
fig, ax1 = plt.subplots(figsize=(12, 5.5))
ax1.bar(range(len(ca_sc)), ca_sc.values, color=sns.color_palette("crest", len(ca_sc)))
ax1.set_ylabel("CA par sous-catégorie")
ax1.set_xticks(range(len(ca_sc)))
ax1.set_xticklabels(ca_sc.index, rotation=45, ha="right", fontsize=8)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
ax2 = ax1.twinx()
ax2.plot(range(len(ca_sc)), ca_cum.values * 100, color="crimson", marker="o", linewidth=2)
ax2.axhline(80, color="grey", linestyle="--", linewidth=1)
ax2.set_ylabel("Part cumulée du CA (%)")
ax2.set_ylim(0, 105)
plt.title("Diagramme de Pareto : concentration du CA par sous-catégorie", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "02_pareto.png"))
plt.close()
print(f"\n{n_80} sous-catégories sur {len(ca_sc)} font 80 % du CA.")

# 6. Synthèse par catégorie
synth_cat = df.groupby("categorie").agg(
    chiffre_affaires=("chiffre_affaires", "sum"),
    marge=("marge", "sum"),
    taux_marge=("taux_marge", "median"),
    part_perte=("vente_a_perte", "mean"),
    nb_lignes=("id_commande", "count"),
).sort_values("chiffre_affaires", ascending=False)
print("\n--- Synthèse par catégorie ---")
print(synth_cat.round(3))

# 7. Heatmap CA par région x catégorie
pivot = df.pivot_table(index="region", columns="categorie", values="chiffre_affaires", aggfunc="sum")
plt.figure(figsize=(8, 5))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={"label": "CA"})
plt.title("Chiffre d'affaires par région et catégorie", fontsize=13, fontweight="bold")
plt.ylabel("Région")
plt.xlabel("Catégorie")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "03_heatmap_region_categorie.png"))
plt.close()

# 8. Marge totale par sous-catégorie : qui crée et qui détruit de la valeur
marge_sc = df.groupby("sous_categorie")["marge"].sum().sort_values()
couleurs = ["#c0392b" if v < 0 else "#27ae60" for v in marge_sc.values]
plt.figure(figsize=(10, 6))
plt.barh(marge_sc.index, marge_sc.values, color=couleurs)
plt.axvline(0, color="black", linewidth=0.8)
plt.title("Marge totale par sous-catégorie : créateurs et destructeurs de valeur",
          fontsize=13, fontweight="bold")
plt.xlabel("Marge totale (rouge = perte nette)")
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
plt.tight_layout()
plt.savefig(os.path.join(FIG, "04_marge_sous_categorie.png"))
plt.close()
destructeurs = marge_sc[marge_sc < 0]
print("\n--- Sous-catégories à marge totale négative (destructeurs de valeur) ---")
print(destructeurs.round(0))

# 9. Performance par segment client
synth_seg = df.groupby("segment_client").agg(
    ca=("chiffre_affaires", "sum"),
    marge=("marge", "sum"),
    panier_moyen=("chiffre_affaires", "mean"),
).sort_values("ca", ascending=False)
print("\n--- Par segment client ---")
print(synth_seg.round(0))
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
synth_seg["ca"].sort_values().plot(kind="barh", ax=axes[0], color=sns.color_palette("crest", 4))
axes[0].set_title("CA par segment client", fontweight="bold")
axes[0].set_xlabel("CA")
axes[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
synth_seg["marge"].sort_values().plot(kind="barh", ax=axes[1], color=sns.color_palette("flare", 4))
axes[1].set_title("Marge totale par segment client", fontweight="bold")
axes[1].set_xlabel("Marge")
axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
plt.tight_layout()
plt.savefig(os.path.join(FIG, "05_segment.png"))
plt.close()

# 10. Export des livrables
df.to_csv(os.path.join(RACINE, "data", "processed", "ventes_enrichies.csv"), index=False, encoding="utf-8")
kpi = pd.DataFrame({
    "indicateur": ["CA total", "Marge totale", "Taux de marge global",
                   "Commandes distinctes", "Panier moyen", "Part lignes à perte"],
    "valeur": [f"{ca_total:,.0f}", f"{marge_totale:,.0f}", f"{taux_marge_global:.1%}",
               f"{nb_commandes:,}", f"{panier_moyen:,.0f}", f"{part_perte:.1%}"],
})
kpi.to_csv(os.path.join(RACINE, "outputs", "reports", "kpi.csv"), index=False)
print("\nGraphiques et exports générés dans outputs/.")
