import sys
import re
import json
import os # Pour manipuler les chemins de fichiers

def convertir_sauts_de_ligne_en_espaces(texte: str) -> str:
    """
    Convertit les sauts de ligne simples en espaces, préserve les sauts de paragraphe,
    réduit les espaces multiples et supprime les espaces superflus en début/fin.
    """
    # Remplace les sauts de ligne qui ne sont pas des séparateurs de paragraphe
    # (c'est-à-dire un \n qui n'est ni précédé ni suivi d'un autre \n) par un espace.
    texte_nettoye = re.sub(r'(?<!\n)\n(?!\n)', ' ', texte)

    # Remplace toute séquence d'un ou plusieurs espaces par un seul espace.
    texte_nettoye = re.sub(r'\s+', ' ', texte_nettoye)

    # Supprime les espaces en début et fin de chaîne.
    texte_nettoye = texte_nettoye.strip()

    return texte_nettoye

def main():
    # Vérifie si un nom de fichier a été fourni en argument.
    if len(sys.argv) < 2:
        print("Usage: python deliner.py <chemin_du_fichier_texte.txt>")
        sys.exit(1)

    chemin_fichier_entree = sys.argv[1]

    # Vérifie si le fichier d'entrée existe.
    if not os.path.exists(chemin_fichier_entree):
        print(f"Erreur : Le fichier '{chemin_fichier_entree}' n'existe pas.")
        sys.exit(1)

    # Détermine le chemin du fichier de sortie JSON.
    # On prend le nom de base du fichier d'entrée et on change l'extension en .json.
    nom_base_fichier = os.path.splitext(os.path.basename(chemin_fichier_entree))[0]
    chemin_fichier_sortie = os.path.join(os.path.dirname(chemin_fichier_entree), f"{nom_base_fichier}.json")

    try:
        # Lecture du contenu du fichier texte.
        with open(chemin_fichier_entree, 'r', encoding='utf-8') as f:
            texte_original = f.read()

        # Traitement du texte.
        texte_traite = convertir_sauts_de_ligne_en_espaces(texte_original)

        # Création de la structure JSON attendue.
        # Le texte traité est placé dans la clé 'chosen' d'un objet unique au sein d'une liste.
        donnees_json = [{"chosen": texte_traite}]

        # Écriture du résultat dans le fichier JSON de sortie.
        with open(chemin_fichier_sortie, 'w', encoding='utf-8') as f:
            json.dump(donnees_json, f, ensure_ascii=False, indent=2)

        print(f"Le fichier '{chemin_fichier_entree}' a été traité et sauvegardé sous '{chemin_fichier_sortie}'.")

    except Exception as e:
        print(f"Une erreur est survenue lors du traitement : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
