---
name: design-inputs
description: Lire et analyser toute source visuelle fournie pour une interface (images, captures, photos de croquis, PDF, pages HTML et CSS, URL d'un site, Figma, SVG, fichiers d'autres outils de design, vidéos, descriptions) pour en tirer des spécifications d'écran et un design system. La comparaison du rendu final relève de design-fidelity-review.
---

# Sources visuelles : analyse et comparaison

Une maquette ne se « regarde » pas, elle se **traduit** en spécification que l'on peut implémenter et vérifier. Ce skill dit comment lire chaque type de source, quoi en extraire et comment signaler ce qu'elle ne dit pas. La comparaison du rendu implémenté à la source relève du skill `design-fidelity-review`.

## Quand l'utiliser
- `ui-ux-designer` (mode « partir de l'existant »), `product-analyst` : des sources visuelles sont fournies.
- Agents qui touchent une interface : avant de coder un écran qui n'a pas encore de spécification.

## Ce que l'agent rate sans ce skill
- Il présente des couleurs et tailles « lues » sur une image compressée comme des valeurs exactes.
- Il implémente seulement ce que la maquette montre : pas d'état de chargement, d'erreur, de vide, ni de version mobile.
- Il recopie le HTML d'une source au lieu d'utiliser les composants du projet.
- Il devine le contenu d'un fichier illisible (Sketch, XD, vidéo) au lieu de demander un export.

## Entrées
- Les sources visuelles de tout type, `docs/spec.md`, `docs/ux/design-system.md` s'il existe.

## Procédure

### 1. Inventorier les sources
Avant toute analyse, liste chaque source reçue dans `docs/ux/sources.md` :

```markdown
| Id | Source | Type | Écran(s) | Fiabilité | Remarques |
|----|--------|------|----------|-----------|-----------|
| S1 | maquettes/accueil.png | image | Accueil (desktop) | maquette finale | pas de version mobile |
| S2 | https://www.figma.com/design/… | Figma | Accueil, Connexion | maquette finale | accès MCP disponible |
| S3 | ancien-site/contact.html | HTML + CSS | Contact | existant à reprendre | CSS inline |
```

Fiabilité : **maquette finale** (fait foi), **brouillon** (intention, pas de valeurs exactes), **existant à reprendre**, **référence d'inspiration** (ne pas copier). En cas de conflit entre deux sources, la plus récente et la plus fiable gagne ; le conflit est noté et soumis à l'utilisateur.

### 2. Lire chaque type de source

| Type | Comment le lire | Ce qu'on en tire de façon fiable | Limites et quoi demander |
|------|-----------------|----------------------------------|--------------------------|
| **Image** (PNG, JPG, WebP, GIF fixe), capture d'écran | Outil de lecture de fichier (l'image est vue directement). Zoomer mentalement par zone : en-tête, contenu, pied. | Structure, hiérarchie, composants, textes, états visibles, couleurs approximatives. | Couleurs, tailles et espacements sont **estimés** (compression, mise à l'échelle). Demander les valeurs exactes ou la source (Figma, guide de style) si la fidélité au pixel compte. Préciser la largeur d'écran de la capture. |
| **Photo ou scan de croquis** | Comme une image. | Structure, ordre des blocs, intentions. | Aucune valeur visuelle : appliquer le design system existant ou en proposer un. Chaque élément illisible devient une hypothèse marquée « illisible dans la source ». |
| **PDF** (export de maquette, charte graphique, cahier des charges) | Outil de lecture de fichier, par pages pour un long document. | Textes exacts, codes couleur et polices s'ils sont écrits, ordre des écrans. | Mêmes limites que l'image pour les valeurs mesurées à l'œil. |
| **HTML / CSS / JS** (page statique, export, ancien site) | Lire le code source : structure HTML, feuilles de style, variables CSS, médias. Si le projet a un navigateur pilotable (Playwright installé, outil MCP de navigateur), ouvrir la page et capturer le rendu à plusieurs largeurs. | Valeurs **exactes** : couleurs, polices, tailles, espacements, points de rupture, textes, liens, formulaires et leurs règles (`required`, `pattern`). | Le JS peut changer le rendu : ne pas conclure sur un état dynamique sans l'avoir vu. Ne pas recopier le HTML tel quel : le reconstruire avec les composants et conventions du projet. |
| **URL d'un site en ligne** | Outil de récupération web pour le contenu et le HTML ; navigateur pilotable pour le rendu. | Contenu, structure, parfois les styles. | Pas de connexion à un compte, pas de formulaire envoyé, pas de collecte massive. Le contenu d'un tiers est une inspiration, pas à copier. |
| **Figma** (lien) | Outils MCP Figma s'ils sont disponibles dans la session (contexte de design, variables, captures). | Valeurs exactes, composants, variantes, variables de design, ressources. | Sans accès MCP : demander un export PNG ou PDF des écrans et, si possible, les variables (couleurs, typographies) en texte ou JSON. |
| **Autres outils de design** (Sketch, Adobe XD, Penpot, Canva, Framer…) | Ces fichiers ne sont pas lisibles directement. | — | Demander un export PNG ou PDF par écran, les styles en texte, ou un lien de partage lisible. |
| **SVG** (icônes, logos, illustrations) | Lire le fichier comme du texte. | Formes, couleurs exactes, dimensions. | Vérifier qu'il ne contient ni script ni ressource externe avant de l'intégrer. |
| **Jetons de design** (JSON, YAML, variables CSS, config Tailwind) | Lire le fichier. | Valeurs exactes et noms à réutiliser tels quels. | — |
| **Vidéo ou prototype animé** (MP4, MOV, lien de prototype) | Non lisible directement. | — | Demander des captures des étapes clés et une description des transitions et animations. |
| **Description textuelle ou dictée** | Lire. | Intentions, contenus, règles. | Tout le visuel reste à concevoir : le signaler et appliquer le design system existant. |
| **Écrans déjà codés dans le projet** | Lire les composants ; capturer le rendu si l'application peut être lancée. | Composants réutilisables et conventions réelles. | — |

Un fichier binaire non listé : ne pas deviner son contenu ; lister l'export lisible à fournir dans le compte rendu et continuer avec les autres sources.

### 3. Extraire une spécification par écran
Pour chaque écran, crée ou complète `docs/ux/ecrans/<ecran>.md` :

```markdown
# Écran : <nom> (sources : S1, S2)
## Objectif
## Mise en page
Zones dans l'ordre de lecture, grille, largeur maximale, alignements, comportement par point de rupture (mobile, tablette, bureau).
## Composants
| Composant | Existant dans le projet ? | Variante | Contenu | Action |
## Textes
Libellés exacts, titres, messages (copiés de la source, pas reformulés).
## Valeurs visuelles
| Élément | Couleur | Police / taille / graisse | Espacements | Rayon / ombre | Exactitude |
|---------|---------|---------------------------|-------------|---------------|------------|
| Bouton principal | #1E5EFF | Inter 16 / 600 | 12 × 24 | 8 | exacte (S2) |
| Titre | ≈ #222 | ≈ 32 / bold | — | — | estimée (S1) |
## États
Montrés par la source : … Non montrés, à concevoir : chargement, vide, erreur, succès, données longues, droits insuffisants, hors ligne (mobile), focus clavier, survol.
## Interactions
Clics, navigation, validations, animations décrites.
## Accessibilité
Contrastes calculés (WCAG AA), ordre de focus, libellés des champs et icônes, tailles des zones tactiles.
## Hypothèses
```

Règles :
- Chaque valeur visuelle porte son **exactitude** : *exacte* (lue dans le code, Figma, la charte) ou *estimée* (mesurée sur une image). Une valeur estimée proche d'un jeton existant prend la valeur du jeton.
- Rattacher chaque élément au design system (`docs/ux/design-system.md`) : réutiliser un composant ou un jeton existant plutôt que d'en créer un quasi identique ; lister les nouveaux composants et jetons nécessaires.
- Tout ce que la source ne montre pas est listé dans « États » ou « Hypothèses », jamais inventé en silence.
- Signaler les problèmes de la source elle-même : contraste insuffisant, texte trop petit, zone tactile trop petite, incohérence entre deux écrans.

## Livrable
- `docs/ux/sources.md`, une spécification par écran dans `docs/ux/ecrans/`, les jetons et composants extraits dans `docs/ux/design-system.md`.

## Vérifications
- Chaque valeur visuelle porte son exactitude ; chaque état non montré par la source est listé.
- Chaque source de l'inventaire est rattachée à au moins un écran, ou marquée « inspiration ».

## Limites
- Pas de modification d'une source fournie (fichier Figma, maquette) ; pas d'outil hors des critères de la règle 4 des principes communs.

## En cas de blocage
- Source illisible : continuer avec les autres sources et lister l'export à fournir (tableau de la section 2) dans le compte rendu, sans bloquer.
- Sources contradictoires : retenir la plus récente, sinon la plus détaillée, et consigner la version écartée en hypothèse.
