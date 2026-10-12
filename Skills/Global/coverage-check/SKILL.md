---
name: coverage-check
description: Vérifier si l'architecture, les stacks et le type de livrable d'un projet sont couverts par les agents et skills installés, et appliquer le mode dégradé quand ils ne le sont pas (agent générique, sources officielles, contrôles renforcés, manque consigné). À utiliser au démarrage d'un projet, à la première tâche sur un dépôt, et quand une décision d'architecture ajoute une brique.
---

# Contrôle de couverture

Les agents et les skills installés couvrent un ensemble précis de stacks et d'architectures. Hors de cet ensemble, un agent qui avance comme si de rien n'était applique des réflexes d'une autre stack et produit du code plausible mais faux. Ce skill fait constater l'écart, le consigner et travailler en mode dégradé, sans bloquer le projet.

## Quand l'utiliser
- `orchestrator` : au démarrage d'un nouveau projet, et à la première demande sur un dépôt (ou si `docs/PROJECT.md` n'a pas de section « Couverture »).
- `architect` : avant de rédiger `docs/architecture.md`, et à chaque ADR qui ajoute une stack, une application ou une brique (file de messages, temps réel, multi-tenant…).
- Tout agent : quand sa tâche touche un dossier, un langage ou un framework qu'aucun agent ni skill installé ne traite.

## Ce que l'agent rate sans ce skill
- Il code un service Go, une API NestJS ou une application Flutter avec les réflexes d'une autre stack, sans le dire.
- Il suppose qu'un skill existe parce que son nom paraît évident, et improvise son contenu.
- Il traite un monorepo comme une seule application et lance les commandes à la racine.
- Personne ne sait, à la fin, quelles parties du livrable ont été produites sans savoir spécialisé.

## Entrées
- Les agents installés (`.claude/agents/*.md` ou `.codex/agents/*.toml`) et les skills installés (`.claude/skills/*/` ou `.agents/skills/*/`).
- Les manifestes du dépôt (`composer.json`, `package.json`, `pom.xml`, `build.gradle*`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `*.csproj`, `pubspec.yaml`, fichiers de workspace), `docs/architecture.md`, `docs/spec.md`.

## Procédure

### 1. Inventorier ce que le projet demande
Relève, pour chaque application du dépôt (une seule si ce n'est pas un monorepo, voir le skill `monorepo`) :
- **Stack** : langage, framework et version (skill `version-compatibility`).
- **Type de livrable** : API ou application web serveur, application web côté client, site public, application mobile, librairie ou SDK publié, outil en ligne de commande, application de bureau, extension de navigateur, traitement de données, fonction serverless.
- **Traits d'architecture** : monorepo, monolithe modulaire, services séparés, traitements asynchrones ou événements, multi-tenant, temps réel, hors ligne, intégration d'un modèle d'IA, infrastructure décrite en code.

Pour un nouveau projet, l'inventaire vient de la spec et des décisions de `architect` ; pour un dépôt existant, des manifestes et de la structure.

### 2. Confronter à ce qui est installé
| Élément demandé | Couvert si… |
|-----------------|-------------|
| Stack | un agent `<framework>-implementer` est installé **et** le skill du framework (`laravel`, `symfony`…) est installé |
| Langage | les skills `coding-conventions-<langage>` et `testing-<langage>` sont installés |
| Trait d'architecture | le skill du trait est installé (`monorepo`, `architecture-patterns`, `background-jobs-events`, `multi-tenancy`, `realtime`) |
| Type de livrable | un agent ou un skill le traite explicitement dans sa description |

Classe chaque élément : **couvert**, **partiel** (agent présent mais skill du framework absent, ou l'inverse), **non couvert**.

### 3. Appliquer le mode dégradé à ce qui n'est pas couvert
Le projet continue ; seule la façon de travailler change.
1. **Agent** : l'implémentation va à `implementer` (générique), avec le chemin de l'application dans le brief. Les agents transverses (`architect`, `test-engineer`, `code-reviewer`, `security-auditor`…) restent utilisables.
2. **Savoir** : l'agent s'appuie sur la documentation officielle de la version installée (`WebFetch` ou la documentation embarquée dans les dépendances) et sur les conventions déjà présentes dans le dépôt, jamais sur sa mémoire seule. Il cite les pages consultées dans son compte rendu.
3. **Contrôles renforcés** : toute tâche de code sur une partie non couverte suit le profil **livraison** pour ses contrôles (`test-engineer` puis `code-reviewer`, plus `security-auditor` si la zone est sensible), même si le changement est petit. Les commandes de lint, de typage et de test sont celles du projet (skill `repository-discovery`) ; sans elles, le résultat est **non vérifié**.
4. **Pas d'improvisation de skill** : un skill absent n'est pas réécrit de mémoire dans le compte rendu ; il est listé comme manquant (étape 4).

### 4. Consigner
- Dans `docs/architecture.md` (par `architect`) ou dans le compte rendu (autres agents, repris par `doc-writer` dans `docs/PROJECT.md`), une section :

```markdown
## Couverture par les agents (AAAA-MM-JJ)
| Élément | Statut | Mode de travail | Skill manquant |
|---------|--------|-----------------|----------------|
| apps/api : Laravel 11 | couvert | laravel-implementer | — |
| apps/web : Vue 3 + Vite | non couvert | implementer + doc officielle, contrôles livraison | vue, testing-typescript |
| Traitements asynchrones | couvert | background-jobs-events | — |
```

- Une entrée de journal qui liste les skills manquants, pour qu'ils puissent être rédigés plus tard dans la bibliothèque.

## Livrable
La table « Couverture par les agents », à jour, et le mode de travail retenu pour chaque partie non couverte.

## Vérifications
- Chaque application et chaque trait d'architecture du projet apparaît dans la table.
- Chaque ligne « non couvert » ou « partiel » a un mode de travail et la liste des skills manquants.
- Les briefs de l'orchestrateur pour une partie non couverte mentionnent le mode dégradé et le profil de contrôle livraison.

## Limites
- Ce skill ne rédige pas les skills manquants et n'en installe pas : il les signale.
- Il ne remet pas en cause une stack imposée par le projet ; il constate seulement comment elle sera traitée.

## En cas de blocage
- Impossible de déterminer la stack (aucun manifeste, dépôt vide) : la décision revient à `architect` ; en attendant, la ligne est « non couvert, à décider ».
- Partie non couverte sans aucune commande de test exécutable : livrer en signalant **non vérifié** et ajouter une tâche « mettre en place les tests de <application> » dans `docs/plan.md`.
