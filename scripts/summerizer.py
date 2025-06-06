import json
import argparse
from pathlib import Path

# Liste des expressions interdites traduites en français
EXPRESSIONS_INTERDITES = [
    'dans ce passage',
    'pour conclure',
    'globalement,',
    'ce chapitre',
    'ce texte',
    'cet extrait',
    'cette section',
    'cette sélection',
    'cette histoire',
    'l\'histoire',
    'ce roman',
    'ce livre',
    '" par ',
    '<|endoftext|>',
    '<|im_start|>',
    '<|im_end|>',
    '###',
    '1.',
    '0:',
    '1:'
]

def valider_contenu(texte: str, titre_livre: str) -> bool:
    """Vérifie la présence de phrases interdites ou du titre du livre"""
    texte_minuscule = texte.lower()
    return not any(
        expr in texte_minuscule
        or f'"{titre_livre}"' in texte_minuscule
        for expr in EXPRESSIONS_INTERDITES
    )

def traiter_chapitre(entree: dict) -> dict:
    """Génère un résumé pour un chapitre donné"""
    # Ici tu intégreras ton appel à l'API OpenAI
    # Exemple simplifié :
    return {
        **entree,
        "resume": "Résumé généré du chapitre..."
    }

def main():
    parser = argparse.ArgumentParser(
        description="Génère des résumés de chapitres depuis un fichier JSON"
    )
    parser.add_argument(
        "fichier_entree",
        type=str,
        help="Chemin vers le fichier JSON d'entrée"
    )

    args = parser.parse_args()

    try:
        # Validation du fichier d'entrée
        chemin_entree = Path(args.fichier_entree)
        if not chemin_entree.exists():
            raise FileNotFoundError(f"Fichier {chemin_entree} introuvable")

        with open(chemin_entree, 'r', encoding='utf-8') as f:
            donnees = json.load(f)

        # Traitement des chapitres
        resultats = [traiter_chapitre(entree) for entree in donnees]

        # Génération du fichier de sortie
        chemin_sortie = chemin_entree.stem + "-summary.json"
        with open(chemin_sortie, 'w', encoding='utf-8') as f:
            json.dump(resultats, f, indent=2, ensure_ascii=False)

        print(f"Résultats enregistrés dans {chemin_sortie}")

    except json.JSONDecodeError:
        print("Erreur: Le fichier d'entrée n'est pas un JSON valide")
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")

if __name__ == "__main__":
    main()
