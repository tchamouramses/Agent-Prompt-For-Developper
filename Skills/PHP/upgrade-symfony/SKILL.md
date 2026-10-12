---
name: upgrade-symfony
description: Monter de version un projet Symfony (mineure ou majeure, d'une LTS à la suivante) en sécurité - corriger toutes les dépréciations sur la dernière mineure avant de changer de majeure, mettre à jour les recettes Flex, aligner Doctrine et les bundles. À utiliser pour toute montée de version de Symfony ou de PHP dans un projet Symfony.
---

# Montée de version Symfony

La méthode générale (filet de tests, étapes courtes, une version majeure à la fois) est dans l'agent `refactorer`. Ce skill donne l'ordre propre à Symfony, qui repose sur une règle : une version majeure ne fait que retirer ce que la dernière mineure précédente a déprécié.

## Quand l'utiliser
- Montée de version mineure ou majeure de Symfony, ou de PHP dans un projet Symfony.
- Un bundle exige une version plus récente de Symfony.

## Ce que l'agent rate sans ce skill
- Il passe à la version majeure suivante sans avoir supprimé les dépréciations sur la dernière mineure (par exemple 6.4 avant 7.0), et doit corriger à l'aveugle des erreurs fatales.
- Il met à jour les paquets `symfony/*` un par un et obtient des versions mélangées.
- Il oublie les recettes Flex : la configuration du projet ne correspond plus aux attentes de la nouvelle version.
- Il ignore Doctrine (ORM 2 vers 3, DBAL 3 vers 4), dont la montée est souvent liée.

## Entrées
- `composer.json` (champ `extra.symfony.require`), `composer.lock`, `symfony.lock`, `config/`, version de PHP, suite de tests.

## Procédure
1. **Préparer** : suite de tests verte et commande citée ; branche dédiée.
2. **Lire** les fichiers `UPGRADE-X.Y.md` du dépôt Symfony pour chaque version entre l'actuelle et la cible, et le guide « Upgrading a Major Version » de la documentation ; liste les points qui touchent le projet.
3. **Monter d'abord à la dernière mineure de la version actuelle** (par exemple 6.4) : `extra.symfony.require` à `6.4.*`, contraintes `symfony/*` alignées, puis `composer update "symfony/*" -W`.
4. **Supprimer toutes les dépréciations** sur cette mineure : barre d'outils de débogage, `bin/console debug:container --deprecations`, journal des dépréciations des tests (`symfony/phpunit-bridge` et `SYMFONY_DEPRECATIONS_HELPER`, ou les rapports de dépréciation de PHPUnit). Le nombre doit atteindre zéro pour le code du projet. Rector avec les ensembles Symfony peut faire les changements mécaniques ; relis son diff.
5. **Changer de majeure** : `extra.symfony.require` à la nouvelle version (`7.4.*`), contraintes alignées, `composer update "symfony/*" -W`. Vérifie la version minimale de PHP requise.
6. **Mettre à jour les recettes Flex** : `composer recipes:update` (une recette à la fois), relis chaque diff et garde les adaptations du projet.
7. **Aligner Doctrine et les bundles** : versions compatibles d'ORM, DBAL, Migrations, API Platform et des bundles tiers ; chacun selon son propre guide.
8. **Vérifier** : `bin/console about`, `lint:container`, `lint:yaml config`, `lint:twig`, `doctrine:schema:validate`, suite complète, analyse statique.
9. **Consigner** dans le journal et un ADR : versions de départ et d'arrivée, étapes, dépréciations corrigées, changements de comportement.

## Livrable
Le projet sur la version cible, sans dépréciation du code du projet, tests verts, une entrée de journal et un ADR, la ligne de CHANGELOG si le comportement visible change.

## Vérifications
- `composer show symfony/framework-bundle` affiche la version cible et tous les paquets `symfony/*` du cœur sont sur la même mineure.
- Aucune dépréciation signalée par les tests pour le code du projet.
- Suite complète verte, résumé cité.

## Limites
- Le changement de version de PHP en production et le déploiement restent des actions réservées (règle 5 des principes communs).

## En cas de blocage
- Bundle sans version compatible : rester sur la version actuelle, consigner le blocage avec le lien vers le suivi du bundle, et proposer un remplaçant selon la règle 4 des principes communs.
- Dépréciation venant d'un paquet tiers : la noter, vérifier qu'une version du paquet la corrige, sinon la laisser en consignant le risque pour la prochaine majeure.
