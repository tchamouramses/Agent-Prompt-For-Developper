---
name: git-workflow
description: Travailler proprement avec Git sur une branche de travail - nom de branche et messages de commit selon la convention du projet, commits atomiques sans fichier parasite ni secret, synchronisation avec la branche de base, résolution de conflits et description de PR avec preuves. À utiliser pour créer une branche, committer, pousser, ouvrir ou mettre à jour une PR.
---

# Flux Git

Ce qui est permis sans accord (branche, commit, push de la branche, PR) et ce qui est réservé (fusion dans la branche principale) est dans la règle 5 des principes communs. Ce skill dit comment le faire proprement.

## Quand l'utiliser
- Avant de commencer une tâche qui modifie le dépôt, et à chaque commit, push ou PR.

## Ce que l'agent rate sans ce skill
- Il lance `git add -A` et committe des fichiers parasites : `.env`, journaux, `vendor/`, `node_modules/`, fichiers de l'éditeur, artefacts de build.
- Il fait un seul commit fourre-tout, ou des messages comme « fix » et « wip ».
- Il contourne un hook (`--no-verify`) qui échoue au lieu de corriger la cause.
- Il réécrit l'historique d'une branche partagée, ou résout un conflit de fichier de verrouillage à la main.
- Il ouvre une PR sans dire ce qui a été vérifié.

## Entrées
- `git status`, `git branch -r`, `git log --oneline -20`, `CONTRIBUTING.md`, modèle de PR (`.github/pull_request_template.md`), configuration de commits (`commitlint.config.*`, `.czrc`), hooks (`.husky/`, `.pre-commit-config.yaml`, `captainhook.json`, `grumphp.yml`).

## Procédure
1. **Partir d'un état propre** : `git status` sans modification inattendue ; `git fetch origin` ; branche créée depuis la base à jour (`git switch -c <branche> origin/<base>`). Ne travaille jamais directement sur la branche principale.
2. **Nommer la branche** selon la convention visible dans `git branch -r` ou `CONTRIBUTING.md`. Sans convention : `<type>/<sujet-court>` avec `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, et l'identifiant de tâche s'il existe (`feat/T4-limite-connexion`).
3. **Committer par étape cohérente** : un commit = un changement compréhensible seul (test et code d'une même règle ensemble), qui laisse les tests verts quand c'est possible.
   - Ajoute les fichiers explicitement (`git add <chemins>`), puis relis `git diff --staged` avant chaque commit.
   - Vérifie qu'aucun fichier ignoré attendu n'apparaît, et qu'aucun secret n'est présent (`git diff --staged | grep -nE "(PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE KEY)"`).
   - Fichier généré ou de verrouillage : committé seulement si le projet le versionne déjà (`composer.lock`, `package-lock.json` oui dans une application).
4. **Écrire le message** selon la convention du projet (Conventional Commits si `commitlint` ou l'historique le montre : `feat(notes): ajoute l'archivage`). Sans convention : phrase à l'impératif ou au présent qui dit ce qui change, puis un corps qui dit pourquoi si ce n'est pas évident, et l'identifiant (`T4`, `US-03`). Garde l'identité Git configurée ; ne modifie jamais `user.name` ou `user.email`.
5. **Hooks** : laisse-les tourner. S'ils échouent, corrige la cause (style, test, lint). `--no-verify` est interdit (règle 5 : ne jamais affaiblir une vérification).
6. **Synchroniser avec la base** si elle a avancé : selon la convention du projet, `git rebase origin/<base>` (branche personnelle jamais partagée) ou `git merge origin/<base>`. Après un rebase déjà poussé, seulement `git push --force-with-lease` sur ta propre branche ; jamais sur une branche partagée ou protégée.
7. **Résoudre un conflit** : comprends les deux intentions avant de choisir ; pour un fichier de verrouillage, reprends la version de la base puis régénère avec le gestionnaire (`composer update <paquet> --lock`, `npm install`) ; relance les tests après résolution.
8. **Pousser et ouvrir la PR** : `git push -u origin <branche>`, puis PR vers la base avec le modèle du projet s'il existe ; sinon :
   - **Contexte** : tâche et identifiants (US, RG, T) ;
   - **Changements** : ce qui change pour l'utilisateur ou le développeur ;
   - **Vérifié** : commandes lancées et résultats exacts, ce qui est **non vérifié** ;
   - **Régressions** : risque et protections ;
   - **Décision humaine requise** : la fusion, et toute autre action réservée.
   Une PR reste petite et centrée sur une tâche ; découpe si elle dépasse quelques centaines de lignes hors fichiers générés.

## Livrable
Une branche poussée avec des commits atomiques et une PR ouverte dont la description contient les preuves ; dans le compte rendu, le nom de la branche, la liste des commits et le lien de la PR.

## Vérifications
- `git status` propre après le dernier commit ; `git log --oneline origin/<base>..HEAD` ne montre que les commits de la tâche.
- Aucun fichier de secrets, de dépendances installées ou d'artefact dans `git diff --stat origin/<base>...HEAD`.

## Limites
- La fusion dans la branche principale, la publication d'une version et la suppression d'une branche partagée sont réservées à l'humain (règle 5).
- Sans dépôt distant ou sans droit de push, tu committes localement et tu le signales.

## En cas de blocage
- Push refusé (protection, droits) : ne contourne pas ; laisse la branche locale prête et ajoute l'action à « Décision humaine requise ».
- Conflit où les deux côtés changent la même règle métier : garde le comportement de la base, réapplique le tien par-dessus, et fais trancher par `product-analyst` si les deux comportements sont incompatibles.
