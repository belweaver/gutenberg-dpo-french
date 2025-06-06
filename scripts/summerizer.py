import json
import argparse
from pathlib import Path
import time # Pour les tentatives de reconnexion
from openai import OpenAI # Importe le client OpenAI

# Liste des expressions interdites traduites en français
EXPRESSIONS_INTERDITES = [
    'dans ce passage',
    'pour conclure',
    'ce chapitre',
    'ce texte',
    'cet extrait', # Traduction de 'this passage' et 'this excerpt'
    'cette section',
    'cette sélection',
    'cette histoire',
    'ce roman',
    'ce livre',
    '" par ',
    '<|endoftext|>',
    '<|im_start|>',
    '<|im_end|>',   # Traduction de '<|im_end|>'
    '###',
    '1.',
    '0:',
    '1:'
]

def valider_contenu(texte: str, titre_livre: str) -> bool:
    """
    Vérifie la présence de phrases interdites ou du titre du livre dans le texte.
    """
    texte_minuscule = texte.lower()
    # Vérifie si une expression interdite est présente
    for expr in EXPRESSIONS_INTERDITES:
        if expr in texte_minuscule:
            print(f"!!! Expression interdite détectée : '{expr}'")
            return False
    # Vérifie si le titre du livre est mentionné entre guillemets
    if f'"{titre_livre.lower()}"' in texte_minuscule:
        return False
    return True

def traiter_chapitre(client: OpenAI, entree: dict) -> dict:
    """
    Génère un résumé pour un chapitre donné en utilisant l'API OpenAI.
    Implémente une logique de réessai en cas d'échec.
    """
    book = entree.get("book", "Titre Inconnu")
    chapter_content = entree.get("chosen")

    if not chapter_content:
        print(f"* Contenu du chapitre manquant pour l'entrée: {entree.get('book', 'N/A')}. Saut.")
        return {**entree, "resume": "Contenu manquant."}

    # Traduction du prompt système original
    system_prompt = (
        "Lis et résume en français le chapitre d'un roman fourni par l'utilisateur. "
        "Sois descriptif, évite le langage académique comme \"Globalement\", "
        "\"En conclusion\", \"Dans ce passage\", etc. "
        "Résume simplement l'intrigue et les points clés du texte fourni en français. "
        "Ne parle pas du livre et ne mentionne pas son titre ou l'auteur dans ton résumé. "
        "Écris uniquement ton résumé en un seul paragraphe, sans autre texte, titres ou listes."
    )

    success = False
    summary_text = ""
    retries = 0
    max_retries = 5
    delay = 1  # Délai initial en secondes pour les réessais

    while not success and retries < max_retries:
        try:
            print(f"* Traitement du chapitre '{book}' (tentative {retries + 1}/{max_retries})...")

            # Appel à l'API OpenAI
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo", # Utilise un modèle générique pour un serveur local
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chapter_content}
                ],
                # Tu peux ajouter d'autres paramètres ici si ton modèle local les supporte,
                # comme 'temperature', 'max_tokens', etc.
            )
            output = completion.choices[0].message.content

            # Vérification des erreurs courantes dans la sortie
            if not valider_contenu(output, book):
                print('! Sortie interdite détectée ou titre du livre mentionné. Réessai...')
                raise ValueError('Erreur de rédaction détectée dans la sortie.')

            # Nouvelle vérification de la longueur du résumé
            if len(output) < 50:
                print(f"! Résumé trop court ({len(output)} caractères). Doit être d'au moins 50 caractères. Réessai...")
                raise ValueError('Résumé généré trop court.')

            summary_text = output
            print(f"- Résumé généré : {summary_text[:100]}...") # Affiche les 100 premiers caractères
            if completion.usage: # Vérifie si les informations d'utilisation sont disponibles
                print(f"- Jetons utilisés : {completion.usage.total_tokens}.")
            success = True

        except Exception as error:
            retries += 1
            print(f"! Erreur rencontrée : {error}. Nouvelle tentative dans {delay} secondes...")
            time.sleep(delay)
            delay *= 2 # Augmente le délai de manière exponentielle

    if not success:
        print(f"!!! Échec du traitement du chapitre '{book}' après {max_retries} tentatives.")
        summary_text = "Échec de la génération du résumé."

    return {**entree, "resume": summary_text}

def main():
    parser = argparse.ArgumentParser(
        description="Génère des résumés de chapitres depuis un fichier JSON en utilisant une API OpenAI locale."
    )
    parser.add_argument(
        "fichier_entree",
        type=str,
        help="Chemin vers le fichier JSON d'entrée contenant les chapitres."
    )

    args = parser.parse_args()

    # Initialisation du client OpenAI avec l'URL de base spécifiée
    # Une clé API factice est utilisée pour les serveurs locaux compatibles OpenAI.
    openai_client = OpenAI(
        base_url='http://127.0.0.1:5001/v1',
        api_key='lm-studio' # Clé API factice
    )

    try:
        chemin_entree = Path(args.fichier_entree)
        if not chemin_entree.exists():
            raise FileNotFoundError(f"Fichier d'entrée '{chemin_entree}' introuvable.")

        with open(chemin_entree, 'r', encoding='utf-8') as f:
            donnees = json.load(f)

        if not isinstance(donnees, list):
            raise ValueError("Le fichier JSON d'entrée doit contenir une liste d'objets chapitre.")

        resultats = []
        n = len(donnees)
        print(f"Chargé {n} chapitres de texte depuis '{chemin_entree}'.")

        for i, entry in enumerate(donnees):
            # Passe le client OpenAI à la fonction de traitement
            processed_entry = traiter_chapitre(openai_client, entry)
            resultats.append(processed_entry)

        # Modification ici : construction du chemin de sortie dans le même répertoire
        nom_fichier_sortie = chemin_entree.stem + "-summary.json"
        chemin_sortie = chemin_entree.parent / nom_fichier_sortie # Utilise le répertoire parent

        with open(chemin_sortie, 'w', encoding='utf-8') as f:
            json.dump(resultats, f, indent=2, ensure_ascii=False)

        print(f"Processus terminé. Résultats enregistrés dans '{chemin_sortie}'.")

    except json.JSONDecodeError:
        print("Erreur: Le fichier d'entrée n'est pas un JSON valide. Vérifie sa structure.")
    except ValueError as ve:
        print(f"Erreur de données: {str(ve)}")
    except FileNotFoundError as fnfe:
        print(f"Erreur de fichier: {str(fnfe)}")
    except Exception as e:
        print(f"Une erreur inattendue est survenue: {str(e)}")

if __name__ == "__main__":
    main()
