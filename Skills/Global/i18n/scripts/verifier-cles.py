#!/usr/bin/env python3
"""Compare les fichiers de traduction d'un projet à la langue de référence.

Signale, pour chaque langue : les clés manquantes, les clés en trop, les valeurs vides
et les variables ({name}, {{name}}, :name, %name%, {0}) absentes ou ajoutées par rapport
à la référence. Les valeurs identiques à la référence sont signalées en avertissement
(texte resté non traduit, ou mot identique dans les deux langues).

Formats lus : JSON (imbriqué ou à plat), .properties (Spring), YAML si PyYAML est installé.
Pour un tableau PHP (Laravel lang/<locale>/*.php), convertis d'abord en JSON :
  php -r 'echo json_encode(require "lang/fr/messages.php");' > /tmp/fr.json

Usage :
  python3 verifier-cles.py <référence> <autre-langue>... [--avertissements-bloquants]
Code de sortie : 1 si une erreur est trouvée (clé manquante, en trop, vide, variable différente).
"""
import json
import re
import sys
from pathlib import Path

VARIABLE = re.compile(r"\{\{\s*[\w.]+\s*\}\}|\{\s*[\w.]+(?=[\s,}])|:[a-zA-Z_]\w*|%[\w.]+%|\{\d+\}")


def aplatir(donnees, prefixe=""):
    sortie = {}
    for cle, valeur in donnees.items():
        chemin = f"{prefixe}.{cle}" if prefixe else str(cle)
        if isinstance(valeur, dict):
            sortie.update(aplatir(valeur, chemin))
        else:
            sortie[chemin] = "" if valeur is None else str(valeur)
    return sortie


def lire_properties(texte):
    donnees, ligne_en_cours = {}, ""
    for brute in texte.splitlines():
        ligne = brute.strip()
        if not ligne_en_cours and (not ligne or ligne[0] in "#!"):
            continue
        if ligne.endswith("\\") and not ligne.endswith("\\\\"):
            ligne_en_cours += ligne[:-1]
            continue
        ligne = ligne_en_cours + ligne
        ligne_en_cours = ""
        morceaux = re.split(r"(?<!\\)\s*[=:]\s*|(?<!\\)\s+", ligne, maxsplit=1)
        donnees[morceaux[0]] = morceaux[1] if len(morceaux) > 1 else ""
    return donnees


def charger(chemin):
    texte = Path(chemin).read_text(encoding="utf-8")
    if chemin.endswith(".properties"):
        return lire_properties(texte)
    if chemin.endswith((".yaml", ".yml")):
        import yaml  # PyYAML ; absent : convertis le fichier en JSON avant
        return aplatir(yaml.safe_load(texte) or {})
    return aplatir(json.loads(texte))


def variables(valeur):
    return sorted(set(VARIABLE.findall(valeur)))


def main(arguments):
    bloquer_avertissements = "--avertissements-bloquants" in arguments
    fichiers = [a for a in arguments if not a.startswith("--")]
    if len(fichiers) < 2:
        print(__doc__)
        return 2
    reference = charger(fichiers[0])
    erreurs = avertissements = 0
    for chemin in fichiers[1:]:
        cible = charger(chemin)
        print(f"== {chemin} (référence : {fichiers[0]})")
        for cle in sorted(reference.keys() - cible.keys()):
            print(f"  ERREUR clé manquante : {cle}")
            erreurs += 1
        for cle in sorted(cible.keys() - reference.keys()):
            print(f"  ERREUR clé en trop (absente de la référence) : {cle}")
            erreurs += 1
        for cle in sorted(reference.keys() & cible.keys()):
            if not cible[cle].strip():
                print(f"  ERREUR valeur vide : {cle}")
                erreurs += 1
            elif variables(reference[cle]) != variables(cible[cle]):
                print(f"  ERREUR variables différentes : {cle} {variables(reference[cle])} -> {variables(cible[cle])}")
                erreurs += 1
            elif cible[cle] == reference[cle] and re.search(r"[^\W\d_]{4,}", cible[cle]):
                print(f"  avertissement identique à la référence : {cle} = {cible[cle]!r}")
                avertissements += 1
    print(f"{len(reference)} clés de référence, {erreurs} erreur(s), {avertissements} avertissement(s)")
    return 1 if erreurs or (bloquer_avertissements and avertissements) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
