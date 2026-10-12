---
name: multi-tenancy
description: Concevoir et coder une application multi-tenant (plusieurs clients, organisations ou espaces isolés dans une même application) - choix du modèle d'isolation, résolution du tenant, filtrage obligatoire des données, cache, fichiers, files d'attente, recherche, migrations et tests d'isolation. À utiliser dès qu'une donnée appartient à une organisation, un compte client ou un espace de travail.
---

# Multi-tenant

Dans une application multi-tenant, une seule requête oubliée qui ne filtre pas par tenant expose les données d'un client à un autre. Ce n'est pas un bug fonctionnel : c'est une fuite de données. Ce skill donne le modèle d'isolation, les points où le tenant se perd, et les tests qui le prouvent.

## Quand l'utiliser
- La spec parle d'organisations, d'entreprises clientes, d'espaces de travail, d'équipes ou de comptes qui ne doivent pas voir les données des autres.
- Ajouter une table, une requête, un cache, un traitement asynchrone, un export ou un fichier dans une application qui a déjà des tenants.
- `security-auditor` et `code-reviewer` : vérifier l'isolation d'un changement.

## Ce que l'agent rate sans ce skill
- Il ajoute une table sans colonne de tenant, ou une requête (liste, recherche, export, compteur, statistique) qui ne filtre pas.
- Il fait confiance à un identifiant de tenant envoyé par le client (paramètre, en-tête, champ de formulaire).
- Il perd le tenant dans une tâche en file d'attente, une commande ou une tâche planifiée, qui s'exécutent sans requête HTTP.
- Il construit une clé de cache, un chemin de fichier ou un index de recherche sans le tenant, et sert les données d'un client à un autre.
- Il pose une contrainte d'unicité globale (`email unique`) alors qu'elle doit l'être par tenant, ou l'inverse.

## Entrées
- `docs/spec.md`, `docs/architecture.md` (modèle d'isolation retenu), le schéma, le mécanisme de résolution du tenant déjà en place.

## Procédure

### 1. Choisir le modèle d'isolation (architect)
| Modèle | Isolation | Coût d'exploitation | Adapté quand |
|--------|-----------|---------------------|--------------|
| Base partagée, colonne `tenant_id` sur chaque table | logique (code) | faible | par défaut : nombreux petits tenants, mêmes fonctionnalités |
| Base partagée + politiques de sécurité au niveau des lignes (PostgreSQL RLS) | logique, garantie par la base | faible à moyen | exigence d'isolation forte sans multiplier les bases |
| Un schéma par tenant | forte | moyen (migrations × tenants) | peu de tenants, exigence contractuelle de séparation |
| Une base par tenant | maximale | élevé | gros clients, données réglementées, hébergement dédié exigé |

Par défaut : base partagée avec colonne de tenant et filtrage automatique, plus RLS si la base est PostgreSQL et que les données sont sensibles. Le choix est consigné en ADR. Une exigence légale ou contractuelle de séparation physique est un choix réservé si la spec ne la tranche pas (règle 5 des principes communs).

### 2. Résoudre le tenant au bon endroit
- Le tenant se déduit d'une source fiable côté serveur : sous-domaine ou domaine, organisation courante de l'utilisateur authentifié (vérifiée contre ses appartenances), jeton signé. Jamais d'un identifiant envoyé librement par le client sans vérifier que l'utilisateur y appartient.
- La résolution a lieu une fois, au début de la requête (middleware, filtre, intercepteur), et place le tenant dans un contexte unique (service à portée de requête). Le reste du code lit ce contexte.
- Sans tenant résolu, une route qui en a besoin répond une erreur ; elle ne revient jamais à « tous les tenants ».

### 3. Filtrer toutes les données par défaut
- Le filtrage est automatique, pas laissé à chaque requête : portée globale (global scope Eloquent, filtre Doctrine, `@Filter` Hibernate ou `@TenantId` si la version le permet), dépôt de base qui ajoute le tenant, ou RLS.
- Les écritures renseignent le tenant automatiquement depuis le contexte (événement de création, valeur par défaut), jamais depuis la saisie.
- Tout contournement du filtre (tâche d'administration globale) est explicite, nommé (`sansFiltreTenant()`), réservé aux rôles d'administration de la plateforme et testé.
- Les requêtes écrites à la main (SQL brut, requêtes de rapport, vues) ajoutent le filtre elles-mêmes ; elles sont relues pour ce point.
- Les relations entre tables vérifient que les deux lignes appartiennent au même tenant (clé étrangère composée avec le tenant, ou contrôle à l'écriture).
- Unicité : décider pour chaque contrainte si elle est globale ou par tenant (`unique(tenant_id, email)`).

### 4. Garder le tenant hors de la requête
- **Files d'attente et événements** : le message transporte l'identifiant du tenant ; le consommateur le replace dans le contexte avant tout accès aux données, et le retire à la fin (skill `background-jobs-events`).
- **Commandes et tâches planifiées** : elles bouclent explicitement sur les tenants, ou reçoivent le tenant en argument.
- **Cache** : la clé contient le tenant ; l'invalidation aussi.
- **Fichiers** : le chemin de stockage commence par le tenant ; l'accès vérifie le tenant avant de servir ou de signer une URL.
- **Recherche et index** : filtre par tenant dans chaque requête de recherche, ou un index par tenant.
- **Journaux et métriques** : le tenant est dans le contexte des journaux, pour diagnostiquer sans croiser les données.
- **Temps réel** : canaux nommés avec le tenant et autorisés côté serveur (skill `realtime`).

### 5. Migrations et données
- Base partagée : une migration ajoute la colonne de tenant et l'index composite (`tenant_id` en tête) sur toute nouvelle table qui porte des données de tenant.
- Schéma ou base par tenant : la migration s'exécute pour chaque tenant, et un échec sur un tenant est rapporté sans bloquer silencieusement les autres (skill `migrations`).

### 6. Tester l'isolation
Pour chaque ressource ajoutée ou modifiée, avec deux tenants A et B créés dans le test :
- un utilisateur de A ne voit pas, ne modifie pas, ne supprime pas et n'exporte pas une donnée de B (réponse 404 ou 403 selon la convention du projet, jamais la donnée) ;
- une liste ou une recherche de A ne contient aucun élément de B ;
- une tâche en file lancée pour A n'agit que sur A ;
- une clé de cache ou un fichier de A n'est pas servi à B.

## Livrable
- `architect` : le modèle d'isolation en ADR, et dans `docs/architecture.md` la résolution du tenant, le mécanisme de filtrage et ses contournements autorisés.
- Agents qui codent : le changement filtré par tenant à tous les points de l'étape 4 touchés, et les tests d'isolation de l'étape 6.

## Vérifications
- Chaque nouvelle table de données de tenant a la colonne de tenant, son index et le filtre automatique (ou la politique RLS).
- Les tests d'isolation de l'étape 6 passent (commande et résultat cités).
- Aucune requête brute, clé de cache, chemin de fichier ou message ajouté sans le tenant (recherche dans le diff).

## Limites
- Les règles de facturation par tenant, les quotas et l'offre commerciale relèvent de la spec.
- La sécurité générale (authentification, autorisation par rôle) est dans les skills de sécurité du langage ; ce skill traite la frontière entre tenants.

## En cas de blocage
- Code existant sans filtrage automatique : ajoute le filtre dans le code que tu touches, écris les tests d'isolation de ta ressource, et signale les autres requêtes non filtrées à `security-auditor` comme tâche prioritaire.
- Modèle d'isolation non décidé et données déjà en production : n'en change pas ; demande l'arbitrage à `architect`, et toute migration des données réelles est une action réservée.
