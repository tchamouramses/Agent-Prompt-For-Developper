---
name: adr
description: Rédiger et tenir les Architecture Decision Records d'un projet au format MADR - un fichier par décision dans docs/adr/NNNN-titre.md, contexte et facteurs de décision, options réellement comparées, décision tranchée et conséquences, statut (proposé, accepté, rejeté, déprécié, remplacé), remplacement d'une décision sans réécrire l'historique. À utiliser pour toute décision structurante (stack, base de données, pattern d'architecture, librairie structurante, convention transverse) et quand une décision passée est remise en cause.
---

# ADR

Les principes communs exigent un ADR pour chaque décision qui structure le projet (règles 2 et 4) et `architect` en rédige un par décision. Ce skill donne le format, la numérotation et le cycle de vie.

## Quand l'utiliser
- `architect` : chaque décision structurante (stack, SGBD, authentification, stockage, communication asynchrone, découpage en modules, convention transverse comme le format des erreurs d'API).
- Tout agent qui choisit une librairie structurante (ORM, framework de test, client HTTP partagé) ou qui revient sur une décision déjà consignée.
- Pas pour : un choix local réversible (nommage, implémentation interne), qui va dans le journal (skill `project-docs-tracking`).

## Ce que l'agent rate sans ce skill
- Il écrit un ADR « décision : on prend X » sans options écartées : six mois plus tard, personne ne sait si Y avait été envisagé.
- Il présente des options de paille (une seule viable, deux absurdes) pour justifier un choix déjà fait.
- Il modifie un ADR accepté pour refléter une nouvelle décision, et efface la trace de l'ancienne.
- Il réutilise un numéro existant ou en saute, parce qu'il n'a pas regardé le dossier.
- Il oublie les conséquences négatives : coût d'exploitation, verrouillage fournisseur, compétence à acquérir, dette créée.
- Il met dans l'ADR le détail d'implémentation qui changera la semaine suivante, au lieu de la décision durable.

## Entrées
- `docs/adr/` existant (numéros, statuts, décisions en vigueur), `docs/spec.md`, `docs/architecture.md`, les contraintes connues (hébergement, budget, compétences, délais), les mesures ou essais réalisés.

## Procédure
1. **Vérifier qu'un ADR est justifié** : la décision est coûteuse à annuler, touche plusieurs modules ou impose une convention aux autres agents. Sinon, une ligne dans la section « Décisions » du journal suffit.
2. **Lire les ADR existants** : `ls docs/adr/` puis le statut de ceux du même sujet. Si une décision en vigueur couvre déjà le sujet, soit tu l'appliques, soit tu la remplaces (point 7) ; jamais deux ADR acceptés contradictoires.
3. **Numéroter** : numéro suivant sur 4 chiffres (`ls docs/adr | sort | tail -1`), titre court à l'impératif ou au nominal en minuscules et tirets : `0007-utiliser-postgresql.md`. Le premier ADR d'un projet peut être `0001-consigner-les-decisions-en-adr.md`.
4. **Écrire le contexte** : le problème en deux à cinq phrases, les contraintes et les facteurs de décision (sécurité, coût, compétences de l'équipe, réversibilité, performance attendue), chiffrés quand c'est possible.
5. **Comparer 2 ou 3 options réelles**, dont le statu quo s'il existe. Pour chacune : avantages, inconvénients, coût d'exploitation, réversibilité. Une option payante ou à coût récurrent est proposée avec une alternative sans coût (règle 5).
6. **Trancher** : une décision, la raison principale rattachée aux facteurs du point 4, et les conséquences positives, négatives et les actions qui en découlent (tâches à ajouter à `docs/plan.md`). Statut :
   - `accepté` quand la décision ne dépend d'aucune action réservée ;
   - `proposé` quand elle attend une décision humaine (coût, compte tiers, licence) : l'ADR devient la pièce jointe de la demande ;
   - `rejeté` pour garder la trace d'une option examinée puis écartée à part entière.
7. **Remplacer, ne jamais réécrire** : un ADR accepté n'est plus modifié sur le fond. Pour changer de décision, crée un nouvel ADR qui cite l'ancien (« Remplace ADR-0003 »), puis change uniquement la ligne de statut de l'ancien en `remplacé par ADR-0009`. Une décision devenue sans objet passe en `déprécié` avec la raison. Seules les corrections de forme (faute, lien cassé) sont permises sur un ADR accepté.
8. **Relier** : ajoute la ligne dans la section « Décisions clés » proposée pour `docs/PROJECT.md` (signalée dans le compte rendu, skill `project-docs-tracking`) et cite le numéro dans `docs/architecture.md` et dans le journal.

## Livrable
`docs/adr/NNNN-titre.md`, compatible MADR :
```markdown
# NNNN. <Titre de la décision>
- Statut : accepté | proposé | rejeté | déprécié | remplacé par ADR-NNNN
- Date : AAAA-MM-JJ
- Décideurs : <agent ou rôle> ; remplace : ADR-NNNN (si applicable)

## Contexte
<Problème, contraintes, ce qui force à décider maintenant.>

## Facteurs de décision
- <facteur mesurable ou vérifiable>

## Options étudiées
### Option A — <nom>
- Pour : … / Contre : … / Coût d'exploitation : … / Réversibilité : …
### Option B — <nom>
- …

## Décision et raison
Option retenue : <A>, parce que <raison rattachée aux facteurs>.

## Conséquences
- Positives : …
- Négatives et dette acceptée : …
- Actions : <tâches ajoutées au plan, avec identifiant>
```

## Vérifications
- Numéro unique et consécutif : `ls docs/adr` ne montre ni doublon ni trou introduit.
- Au moins deux options réelles, chacune avec un inconvénient écrit.
- Aucun ADR accepté contradictoire sur le même sujet ; chaque ADR remplacé pointe vers son successeur et inversement.
- Le diff d'un ADR accepté ancien ne touche que sa ligne de statut.

## Limites
- L'ADR consigne une décision ; il ne remplace ni `docs/architecture.md` (vue d'ensemble) ni la spec.
- Un ADR `proposé` n'autorise pas l'action réservée qu'il décrit : seul l'accord humain tracé le fait.

## En cas de blocage
- Information manquante pour départager : retiens l'option la plus réversible (skill `autonomy-policy`), écris l'hypothèse dans le contexte et la condition qui ferait revoir la décision.
- Projet existant sans ADR mais avec des choix déjà en place : ne rédige pas l'histoire a posteriori ; crée seulement les ADR des décisions que ta tâche touche, avec le contexte constaté dans le code.
