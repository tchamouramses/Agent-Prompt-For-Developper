---
name: architecture-patterns
description: Choisir, décrire et faire respecter l'organisation interne du code (couches du framework, monolithe modulaire, hexagonale ou ports et adaptateurs, Clean Architecture, DDD tactique, CQRS, services séparés) - critères de choix, correspondance dans chaque framework, règles de dépendance vérifiées par un outil. À utiliser pour concevoir un projet, ajouter un module, ou coder dans un projet qui suit déjà un de ces modèles.
---

# Modèles d'architecture du code

L'agent `architect` décide du modèle et le consigne en ADR ; les agents qui codent le suivent. Ce skill donne les critères pour choisir un modèle proportionné, la façon de le reconnaître dans un code existant et les règles qui le font tenir dans la durée.

## Quand l'utiliser
- `architect` : nouveau projet, nouveau module, ou code qui devient difficile à faire évoluer.
- Agents qui codent : avant de créer un fichier dans un projet structuré en modules, en couches de domaine ou en ports et adaptateurs.
- `code-reviewer` : vérifier qu'un changement respecte les dépendances autorisées.

## Ce que l'agent rate sans ce skill
- Il plaque une architecture hexagonale ou DDD complète sur un CRUD de dix écrans : trois fois plus de fichiers, aucun bénéfice.
- À l'inverse, il met des règles métier dans les contrôleurs, les composants ou les requêtes d'un projet qui a une couche de domaine.
- Il ne reconnaît pas le modèle en place et crée un fichier au mauvais endroit (un service global dans un projet découpé en modules, un appel à l'ORM depuis le domaine).
- Il découpe en services séparés pour « préparer la montée en charge », avec des appels réseau, des transactions distribuées et des déploiements multiples sans besoin.
- Il décrit des règles de dépendance que rien ne vérifie, et elles sont violées au bout de trois semaines.

## Entrées
- `docs/spec.md`, `docs/architecture.md`, les ADR, la structure du code existant.

## Procédure

### 1. Reconnaître le modèle en place (projet existant)
| Indice dans le code | Modèle probable |
|---------------------|-----------------|
| Dossiers techniques du framework seulement (`Controllers/`, `Models/`, `Services/`, `components/`) | couches du framework |
| Dossiers par domaine métier (`Billing/`, `Catalog/`, `modules/orders/`), chacun avec ses couches | monolithe modulaire |
| `Domain/`, `Application/`, `Infrastructure/` ; interfaces `*Repository` ou `*Port` dans le domaine, implémentations dans l'infrastructure | hexagonale ou Clean Architecture |
| Agrégats, objets valeur, événements de domaine, `*Id` typés | DDD tactique |
| `Commands/` et `Queries/` séparés, gestionnaires dédiés, parfois deux modèles de lecture et d'écriture | CQRS |
| Plusieurs applications déployées séparément qui s'appellent par le réseau ou par messages | services séparés |

Suis le modèle trouvé, même incomplet. Si deux modèles coexistent, suis celui du module que tu modifies et signale l'incohérence sans la corriger hors de ta tâche.

### 2. Choisir un modèle (nouveau projet ou nouveau module)
Pars du plus simple et ne monte d'un niveau que si un critère de la colonne de droite est vrai **aujourd'hui** (spec ou code existant), pas « plus tard ».

| Modèle | Adapté quand | Monter au suivant si |
|--------|--------------|----------------------|
| Couches du framework (contrôleur fin, service ou action, modèle) | CRUD, back-office, MVP, une petite équipe | plusieurs domaines métier avec des règles qui se croisent, ou plus d'une dizaine d'entités |
| Monolithe modulaire (un module par domaine, interface publique par module) | plusieurs domaines, une seule application déployée | règles métier complexes à tester sans base, ou infrastructure appelée à changer (fournisseur de paiement, stockage) |
| Hexagonale / Clean Architecture dans les modules qui le demandent | logique métier riche, plusieurs entrées (API, file, commande), dépendances externes remplaçables | invariants métier forts et vocabulaire métier précis |
| DDD tactique dans ces modules (agrégats, objets valeur, événements de domaine) | invariants à garantir dans une transaction, langage métier partagé avec les experts | lecture et écriture aux besoins très différents |
| CQRS (commandes et requêtes séparées, éventuellement modèle de lecture dédié) | écrans de lecture lourds ou dénormalisés, écritures avec règles fortes | — |
| Services séparés | équipes indépendantes, besoins d'échelle ou de disponibilité très différents par partie, contrainte technique (autre langage) | — |

Règles :
- Le modèle peut varier par module : un module de paiement hexagonal et un module de paramètres en couches simples coexistent dans un monolithe modulaire.
- Les services séparés exigent un ADR qui montre le besoin, le coût (réseau, cohérence éventuelle, observabilité, déploiements) et pourquoi un monolithe modulaire ne suffit pas. Sans ce besoin, l'option retenue est le monolithe modulaire.
- Le CQRS ne signifie pas event sourcing ; l'event sourcing demande un ADR à part.

### 3. Correspondance dans les frameworks
| Framework | Couches du framework | Monolithe modulaire | Hexagonale / Clean |
|-----------|----------------------|---------------------|--------------------|
| Laravel | `app/Http`, `app/Models`, `app/Actions` ou `app/Services` | `app/Modules/<Domaine>/` ou `src/<Domaine>/` (autoload PSR-4), un service provider par module | `Domain/` sans Eloquent, `Infrastructure/` avec les modèles Eloquent et les implémentations des dépôts |
| Symfony | `src/Controller`, `src/Entity`, `src/Service` | `src/<Domaine>/` avec ses sous-dossiers, configuration des services par module | entités Doctrine mappées en XML ou attributs dans `Infrastructure`, ou entités du domaine mappées directement si le projet l'accepte (consigné en ADR) |
| Spring Boot | `controller`, `service`, `repository` | un paquet par domaine (`com.exemple.billing`), visibilité package-private pour l'interne ; Spring Modulith si présent | `domain` sans annotation Spring ni JPA, `adapter.in` / `adapter.out` |
| Angular | `components`, `services` | un dossier par fonctionnalité (`features/<domaine>`), composants autonomes, routes chargées à la demande | services de domaine sans dépendance à `HttpClient`, adaptateurs d'accès aux données |
| Next.js | `app/`, `components/`, `lib/` | `features/<domaine>/` (composants, actions serveur, accès aux données) | logique métier dans des fonctions pures sans dépendance à Next, accès aux données derrière une interface |
| Expo | `app/` (routes), `components/`, `hooks/` | `features/<domaine>/` | même principe que Next.js |

### 4. Règles de dépendance
Pour le modèle retenu, écris dans `docs/architecture.md` :
- les modules ou couches et ce que chacun expose ;
- les dépendances autorisées (le domaine ne dépend ni du framework ni de l'infrastructure ; un module n'utilise un autre module que par son interface publique ; pas de dépendance circulaire) ;
- la communication entre modules : appel de l'interface publique, ou événement de domaine (skill `background-jobs-events`) si l'émetteur n'a pas à connaître les destinataires.

Fais vérifier ces règles par un outil dès qu'il y a plus d'une couche ou d'un module, choisi selon le skill `autonomy-policy` : par exemple Deptrac pour PHP, ArchUnit ou Spring Modulith pour Java, dependency-cruiser ou les règles de frontières d'ESLint pour TypeScript. L'outil tourne dans la CI.

### 5. Coder dans le modèle
- Un nouveau cas d'usage se place dans le module de son domaine ; s'il en traverse deux, il appartient au module qui porte la décision métier et appelle l'autre par son interface.
- Les règles métier vivent dans la couche prévue (service, action, entité ou agrégat), jamais dans un contrôleur, un composant, une requête SQL ou un écouteur technique.
- Dans un modèle hexagonal, toute nouvelle dépendance externe (API tierce, stockage, horloge si elle est testée) passe par un port défini dans le domaine et un adaptateur dans l'infrastructure.
- Les tests suivent les couches : domaine en tests unitaires sans base ni framework, adaptateurs en tests d'intégration, parcours en tests de bout en bout (skill `testing-strategy`).

## Livrable
- `architect` : le modèle retenu par module, ses règles de dépendance dans `docs/architecture.md`, un ADR, l'outil de vérification choisi.
- Agents qui codent : le code placé dans la bonne couche, et dans le compte rendu le modèle suivi et toute incohérence relevée.

## Vérifications
- L'outil de vérification des dépendances passe (commande et résultat cités) ; sans outil, `code-reviewer` vérifie les imports des fichiers modifiés.
- Aucun fichier du domaine n'importe le framework, l'ORM ou un client HTTP quand le modèle l'interdit.
- Chaque niveau de modèle au-dessus des couches du framework est justifié par un critère vrai aujourd'hui, cité dans l'ADR.

## Limites
- Le découpage du schéma de base et la propriété des tables par module sont traités par `data-modeler` (skill `db-schema-design`).
- La communication asynchrone entre modules ou services est détaillée dans `background-jobs-events` ; l'isolation des clients dans `multi-tenancy`.

## En cas de blocage
- Le modèle en place empêche la tâche (dépendance circulaire existante, module qui expose tout) : réalise la tâche dans le respect du modèle autant que possible, et propose la correction structurelle comme tâche du plan pour `refactorer`.
- Désaccord sur le modèle entre agents : `architect` tranche par un ADR.
