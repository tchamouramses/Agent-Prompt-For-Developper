---
name: changelog-semver
description: Tenir le changelog au format Keep a Changelog et fixer le numéro de version selon SemVer - lignes écrites pour l'utilisateur, rubriques exactes, section Unreleased, passage d'Unreleased à une version datée, liens de comparaison, numéro aligné dans les fichiers de version, cas 0.x et préversions. À utiliser pour relire ou consolider docs/CHANGELOG.md, préparer une version, ou décider si un changement est majeur, mineur ou correctif.
---

# Changelog et versions

L'ajout d'une ligne dans `docs/CHANGELOG.md` en fin de tâche est décrit par le skill `project-docs-tracking` (rubriques, section `[Unreleased]`, gabarit initial). Ce skill couvre la consolidation et le passage à une version ; publier la version (tag poussé, release, paquet) est réservé à l'humain (règle 5 des principes communs).

## Quand l'utiliser
- `doc-writer` : consolidation du changelog, préparation d'une version (étape 7 de son rôle).
- `devops-engineer` : vérification du changelog avant une liste de déploiement (skill `deployment-checklist`).
- Tout agent qui hésite sur la nature d'un changement (cassant ou non).

## Ce que l'agent rate sans ce skill
- Il génère le changelog depuis les messages de commit : refactorings, tests et « fix typo » y entrent, les changements visibles décrits dans le journal n'y sont pas.
- Il passe en mineur un changement cassant (champ d'API retiré, variable d'environnement renommée, PHP minimal relevé) parce que « c'est petit ».
- Il renomme `[Unreleased]` en version sans recréer une section `[Unreleased]` vide au-dessus, ou invente la date.
- Il réécrit des entrées de versions publiées, ou fusionne deux versions.
- Il change le numéro dans le changelog mais pas dans `package.json`, `build.gradle` ou `app.json`, ou en ajoute un dans `composer.json` qui n'en avait pas.
- Il crée et pousse le tag lui-même.

## Entrées
- `docs/CHANGELOG.md` (ou le `CHANGELOG.md` racine si le projet le tient là), les entrées de `docs/journal/` depuis la dernière version, `git log <dernier-tag>..HEAD`, `git tag --sort=-v:refname | head`.
- Les fichiers qui portent la version : `package.json`, `pom.xml`, `build.gradle`, `app.json` ou `app.config.ts` (Expo), constante applicative éventuelle.

## Procédure
1. **Rassembler les changements** depuis le dernier tag : section `[Unreleased]`, journal, diff (`git diff <dernier-tag>..HEAD --stat`). Le journal et le diff font foi ; les messages de commit servent seulement à ne rien oublier.
2. **Relire chaque ligne** : une phrase pour l'utilisateur du produit ou de l'API, au passé ou à l'indicatif, avec la référence (`(T4)`, `(US-03)`). Retire ce qui n'est pas visible ; fusionne les doublons ; vérifie la rubrique (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`). Un changement cassant commence par `**Rupture :**` et dit quoi faire.
3. **Fixer le niveau** à partir de la version courante `X.Y.Z` :

| Changement | 1.0.0 et plus | 0.y.z |
|------------|---------------|-------|
| Rupture pour un consommateur : API (skill `api-contracts`), configuration ou variable renommée, prérequis relevé, donnée migrée sans retour, comportement attendu modifié | majeur `X+1.0.0` | mineur `0.Y+1.0` |
| Ajout compatible, dépréciation annoncée | mineur `X.Y+1.0` | correctif ou mineur, selon la convention du projet |
| Correction sans changement de contrat | correctif `X.Y.Z+1` | correctif |

   Une seule rupture suffit pour un majeur. Préversion : `2.0.0-rc.1`, puis `rc.2`, puis `2.0.0`. Le passage à `1.0.0` est une décision de produit : propose-le, ne le fais pas seul.
4. **Créer la section de version** : déplace le contenu de `[Unreleased]` sous `## [X.Y.Z] - AAAA-MM-JJ` (date du jour de la préparation, à corriger par l'humain s'il publie un autre jour), laisse `## [Unreleased]` vide au-dessus, mets à jour les liens de comparaison en bas du fichier.
5. **Aligner les fichiers de version** existants : `npm version X.Y.Z --no-git-tag-version`, `<version>` du `pom.xml` (`./mvnw versions:set -DnewVersion=X.Y.Z -DgenerateBackupPoms=false` si le plugin est utilisable), `version` de `build.gradle`, `expo.version` de `app.json` (le numéro de build iOS et Android suit la convention du projet). N'ajoute pas de champ `version` à `composer.json` : le tag fait foi pour Composer.
6. **Préparer la publication** pour l'humain : commande de tag (`git tag -a vX.Y.Z -m "vX.Y.Z"` puis `git push origin vX.Y.Z`), texte de release copié de la section, dans le bloc « Décision humaine requise ».

## Livrable
```markdown
## [Unreleased]

## [2.0.0] - 2026-10-12
### Added
- Export des factures au format CSV depuis la liste des factures. (US-12)
### Changed
- **Rupture :** le champ `amount` de `GET /api/v1/invoices` est un entier en centimes ; lire `amount` / 100. (T31)
### Fixed
- Les rappels ne sont plus envoyés deux fois après une relance de la file. (T29)

[Unreleased]: https://<forge>/<dépôt>/compare/v2.0.0...HEAD
[2.0.0]: https://<forge>/<dépôt>/compare/v1.4.2...v2.0.0
```

## Vérifications
- `git diff docs/CHANGELOG.md` ne modifie aucune section de version déjà publiée.
- Chaque ligne a une référence ; chaque rupture du diff (contrat, configuration, prérequis) a sa ligne et correspond au niveau choisi.
- Le même numéro figure dans le changelog et dans chaque fichier de version du projet (`rg -n "X\.Y\.Z"` cité).

## Limites
- Créer ou pousser un tag, publier une release ou un paquet, soumettre aux stores : actions réservées (règle 5).
- Les messages de commit conventionnels et les outils de release automatique ne s'ajoutent que si le projet les utilise déjà.

## En cas de blocage
- Impossible de savoir si un consommateur dépend du comportement changé : traite-le comme une rupture (majeur) et consigne l'hypothèse.
- Historique incohérent (versions sans tag, tags sans section) : ne réécris pas le passé ; documente l'écart dans le journal et repars de la dernière version cohérente.
