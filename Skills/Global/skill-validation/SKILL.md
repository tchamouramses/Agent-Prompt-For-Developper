---
name: skill-validation
description: Vérifier un skill de cette bibliothèque avant de le publier - structure et contrat, description qui déclenche au bon moment, références valides, scripts qui fonctionnent, et comportement sur des cas d'essai. À utiliser quand on crée ou modifie un skill dans Skills/.
---

# Validation des skills

## Quand l'utiliser
- Création ou modification d'un skill dans `Skills/`.
- Renommage d'un skill (les agents qui le citent doivent suivre).

## Ce que l'agent rate sans ce skill
- Une description vague (« aide pour les tests ») qui ne se déclenche jamais, ou trop large, qui se déclenche partout.
- Un skill qui répète ce que le modèle sait déjà au lieu d'apporter ce qu'il rate.
- Des références cassées : skill cité par un agent mais inexistant, chemin ou script introuvable.
- Un skill jamais essayé sur un cas réel.

## Entrées
- Le dossier du skill (`Skills/<Global|Langage>/<nom>/SKILL.md` et ses fichiers), les agents qui le citent.

## Procédure
1. **Contrôle automatique** : `python3 scripts/validate-skills.py`. Il vérifie :
   - en-tête YAML avec `name` identique au nom du dossier (minuscules, chiffres, tirets) et `description` non vide de moins de 1 024 caractères ;
   - présence des sections du contrat : « Quand l'utiliser », « Ce que l'agent rate sans ce skill », « Entrées », « Procédure », « Livrable », « Vérifications », « Limites », « En cas de blocage » ;
   - noms de skills uniques dans toute la bibliothèque ;
   - chaque skill cité dans le champ `skills:` d'un agent existe ou figure au catalogue (`docs/catalogue.md`) comme prévu.
2. **Relire la description** comme le modèle qui doit choisir : elle dit *ce que fait* le skill et *quand l'utiliser*, avec les mots que l'utilisateur ou l'agent emploieront. Elle ne recouvre pas celle d'un autre skill.
3. **Relire « Ce que l'agent rate »** : chaque point doit être une erreur réelle et fréquente. Si la section est vide ou générique, le skill n'apporte probablement rien : le fusionner ou l'abandonner.
4. **Vérifier la cohérence avec les principes** : le skill détaille une règle des principes sans la contredire ni la réécrire ; il la cite.
5. **Taille** : le `SKILL.md` reste lisible d'une traite (repère : moins de 300 lignes). Les détails longs (tables de référence, exemples par framework) vont dans des fichiers à côté, cités depuis le `SKILL.md` et chargés seulement au besoin.
6. **Scripts** : tout script fourni s'exécute sur un cas d'exemple, sans dépendance non déclarée, et documente son usage.
7. **Cas d'essai** : au moins deux demandes réalistes où le skill doit se déclencher et une où il ne doit pas. Pour chacune, vérifier sur un projet d'essai que l'agent l'utilise (ou non) et que le résultat respecte la section « Livrable ». Consigner les cas et le résultat dans le compte rendu.

## Livrable
Le skill corrigé, la sortie de `scripts/validate-skills.py`, et les cas d'essai avec leur résultat (ou « non vérifié » si aucun projet d'essai n'était disponible).

## Vérifications
- `python3 scripts/validate-skills.py` termine sans erreur.
- `python3 scripts/sync-agents.py --check` termine sans erreur si des agents ont été modifiés.

## Limites
- Le contrôle automatique vérifie la forme, pas la qualité : les étapes 2 à 7 restent nécessaires.

## En cas de blocage
- Deux skills se recouvrent : fusionne-les ou partage clairement les responsabilités, et consigne le choix avec les deux descriptions côte à côte.
