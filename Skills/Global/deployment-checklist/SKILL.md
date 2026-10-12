---
name: deployment-checklist
description: Préparer un déploiement pour que l'humain n'ait qu'à l'accepter - prérequis vérifiés, inventaire de ce qui change (migrations, variables, files, tâches planifiées, caches), ordre des étapes, migrations compatibles avec l'ancien code, sauvegarde et restauration, vérifications de santé, critères d'annulation et retour arrière écrit et testé hors production. À utiliser avant toute mise en production ou tout déploiement sur un environnement partagé, et pour rédiger la partie déploiement de docs/runbook.md.
---

# Liste de déploiement

Le déploiement en production ou sur un environnement partagé est une action réservée (règle 5 des principes communs) ; l'agent `devops-engineer` le prépare (étape 8 de son rôle). Ce skill dit quoi vérifier et quoi écrire pour que l'humain puisse accepter, exécuter et annuler sans aide.

## Quand l'utiliser
- `devops-engineer` : préparation d'une version, après un rapport `quality-gatekeeper` « Accepté ».
- `orchestrator` : fin d'un parcours de livraison, pour regrouper la décision humaine de mise en production.

## Ce que l'agent rate sans ce skill
- Il déploie le code et la migration qui retire une colonne en même temps : pendant la bascule, l'ancien code tourne encore et casse.
- Il oublie de redémarrer les workers (`queue:restart`, `messenger:stop-workers`) : ils continuent d'exécuter l'ancien code pendant des heures.
- Il oublie une nouvelle variable d'environnement : l'application démarre et échoue au premier appel.
- Il prévoit le retour arrière « par `migrate:rollback` » alors que le `down()` perd des données écrites depuis.
- Il écrit « vérifier que tout marche » au lieu de critères mesurables de succès et d'annulation.
- Il construit l'image ou le bundle front par environnement sans le dire, et déploie en production un build fait pour la pré-production.
- Il « fait juste la migration » lui-même sur la base partagée.

## Entrées
- Rapport de livraison (`docs/livraisons/`), section de version du changelog (skill `changelog-semver`), diff depuis la dernière version déployée, `docs/runbook.md`, `.env.example`, migrations ajoutées, `docs/architecture.md` (hébergement, nombre d'instances).

## Procédure
1. **Vérifier les prérequis** : rapport « Accepté » sur le commit exact, CI verte sur ce commit, version et changelog prêts, passage prévu par la pré-production avec les parcours critiques validés par `e2e-validator`.
2. **Inventorier ce qui change** depuis la dernière version déployée (`git diff <tag-déployé>..<commit> --stat`) : migrations, nouvelles variables (`git diff <tag-déployé>..<commit> -- .env.example`), dépendances système, files et workers, tâches planifiées, caches à invalider, changements de contrat d'API (skill `api-contracts`).
3. **Classer les migrations** (skill `migrations`) : compatibles avec l'ancien code (déployables avant le code), ou non (alors le déploiement est refusé tel quel : découper en étendre puis contracter). Estimer la durée et les verrous sur les grosses tables.
4. **Sauvegarde** : vérifier qu'une sauvegarde récente existe et qu'une restauration a déjà été testée ; sinon, l'inscrire comme étape préalable de la décision humaine.
5. **Écrire l'ordre des étapes**, commandes exactes par stack :
   - Laravel : `composer install --no-dev --optimize-autoloader`, `php artisan migrate --force`, `php artisan optimize`, `php artisan queue:restart` ; `php artisan down` seulement si une migration l'exige.
   - Symfony : `composer install --no-dev --optimize-autoloader`, `bin/console doctrine:migrations:migrate --no-interaction`, `bin/console cache:clear --env=prod`, `bin/console messenger:stop-workers`.
   - Spring Boot : image ou jar versionné ; migrations Flyway ou Liquibase au démarrage : avec plusieurs instances, vérifier le verrou de l'outil ou lancer la migration une fois avant.
   - Angular, Next.js : build fait pour l'environnement cible (variables figées au build), assets servis avant le HTML qui les référence.
   - Expo : changement JavaScript seul → mise à jour OTA compatible avec le `runtimeVersion` publié ; changement natif → nouveau build et soumission aux stores, action réservée distincte.
6. **Définir la santé et les critères** : endpoint de santé (`/up`, `/actuator/health`), parcours de fumée à rejouer (3 à 5, issus des critères Must), seuils d'annulation chiffrés (taux d'erreurs 5xx, latence, file qui grossit) et durée d'observation.
7. **Écrire le retour arrière** : version précédente redéployée (tag ou image précédente), sort des migrations (compatibles donc laissées en place, ou `down` sans perte prouvé en test), caches et workers à relancer. Tester ce retour arrière sur un environnement local ou de test et citer la preuve.
8. **Rendre la décision humaine** avec le gabarit ci-dessous ; mets la procédure durable (étapes génériques, retour arrière) dans `docs/runbook.md`.

## Livrable
Fichier `docs/livraisons/AAAA-MM-JJ-vX.Y.Z-deploiement.md`, repris dans le bloc « Décision humaine requise » :
```markdown
# Déploiement vX.Y.Z — <commit>
- Prérequis : rapport <lien> Accepté · CI <run> verte · changelog [X.Y.Z] · pré-production validée <date ou à faire>
- Change : migrations <liste, compatibles oui/non, durée> · variables <noms, sans valeur> · workers/cron <…>
- Avant : sauvegarde <où, date> · restauration testée <date>
- Étapes : 1. … 2. … (commandes exactes)
- Santé : <endpoint> 200 · parcours de fumée <liste>
- Annuler si : <seuils chiffrés> pendant <durée>
- Retour arrière : 1. … 2. … — testé : <commande et résultat>
```

## Vérifications
- Chaque commande de la liste existe dans le projet et a été exécutée en local ou en test (les commandes de production restent **non vérifiées** sur la production).
- Chaque migration est classée ; aucune n'exige l'arrêt de l'ancien code sans étape prévue.
- Chaque nouvelle variable de `.env.example` apparaît dans la liste, sans valeur.

## Limites
- Exécuter le déploiement, la migration de production, la sauvegarde ou la restauration réelle, et prévenir les utilisateurs : actions réservées (règle 5).
- Ce skill ne choisit pas l'hébergement ni la stratégie (bleu-vert, progressive) : `architect` les décide.

## En cas de blocage
- Pas de pré-production : signale le risque, propose de la créer (coût éventuel : décision humaine) et renforce les parcours de fumée.
- Retour arrière impossible sans perte (migration destructive) : bloque la liste, découpe la migration (skill `migrations`) ou présente la perte comme décision humaine explicite.
