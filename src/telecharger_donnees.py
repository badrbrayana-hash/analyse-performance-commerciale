"""
Téléchargement du jeu de données Superstore Sales.

Source : dataset public "Superstore Sales", hébergé sur GitHub
(https://raw.githubusercontent.com/curran/data/gh-pages/superstoreSales/superstoreSales.csv).

Il s'agit d'un jeu de données public et largement utilisé dans la communauté
data. À l'origine il s'agit d'un jeu d'exemple (et non des transactions d'une
entreprise nommée), mais il est reconnu, réaliste et riche : profit réel par
ligne, remises, sous-catégories, plusieurs régions.

Exécution :
    python src/telecharger_donnees.py

Sortie :
    data/raw/superstore_sales.csv
"""

import os
import urllib.request

URL = ("https://raw.githubusercontent.com/curran/data/gh-pages/"
       "superstoreSales/superstoreSales.csv")


def main():
    ici = os.path.dirname(os.path.abspath(__file__))
    racine = os.path.dirname(ici)
    dossier = os.path.join(racine, "data", "raw")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, "superstore_sales.csv")

    print("Téléchargement en cours...")
    urllib.request.urlretrieve(URL, chemin)

    taille = os.path.getsize(chemin) / 1024
    print(f"Fichier enregistré : {chemin} ({taille:.0f} Ko)")


if __name__ == "__main__":
    main()
