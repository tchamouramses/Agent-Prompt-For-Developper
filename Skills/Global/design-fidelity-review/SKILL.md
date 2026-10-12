---
name: design-fidelity-review
description: Comparer le rendu implémenté d'un écran à sa référence visuelle (spécification d'écran, maquette, capture, Figma, HTML) à plusieurs largeurs et états, lister les écarts avec leur gravité, puis vérifier leurs corrections. À utiliser après l'implémentation d'une interface et par e2e-validator avant une livraison.
---

# Revue de fidélité au design

La lecture des sources et la spécification d'écran relèvent du skill `design-inputs`. Ce skill commence quand l'écran est implémenté.

## Quand l'utiliser
- Agents qui touchent une interface : après avoir implémenté un écran, avant de rendre la main.
- `e2e-validator` : contrôle indépendant de la conformité au design.
- Après la correction d'écarts signalés : vérifier qu'ils sont levés sans en créer d'autres.

## Ce que l'agent rate sans ce skill
- Il déclare l'écran « conforme à la maquette » sans l'avoir capturé.
- Il compare une seule largeur et un seul état (le nominal, sur bureau).
- Il compare avec des données différentes de la maquette et confond un écart de contenu avec un écart de design.
- Il traite un écart sur une valeur estimée comme un défaut bloquant, ou un élément manquant comme un détail.
- Après correction, il ne recapture que la zone corrigée.

## Entrées
- `docs/ux/ecrans/<écran>.md` (avec l'exactitude de chaque valeur) et les sources citées.
- L'application lancée en local ou en environnement de test, avec des données de démonstration proches de celles de la maquette.

## Procédure
1. **Préparer** : mêmes données que la source autant que possible (textes, nombre d'éléments, images), même thème (clair ou sombre), polices chargées, animations désactivées ou terminées.
2. **Capturer le rendu** avec l'outil déjà présent dans le projet (Playwright, Maestro, Detox, outil MCP de navigateur) :
   - aux largeurs de la source, et au minimum 375 px et 1280 px pour le web ; pour le mobile, un petit et un grand écran, iOS et Android si possible ;
   - pour chaque état spécifié : nominal, chargement, vide, erreur, succès, données longues, focus clavier, survol si la source le montre.
   Sans outil de capture, installe l'outil standard selon la règle 4 des principes communs (Playwright pour le web) ; si c'est impossible, marque la comparaison **non vérifiée**.
3. **Comparer zone par zone** avec la source et la spécification : structure et ordre des blocs, présence de chaque composant, textes exacts, couleurs, typographie (police, taille, graisse, interligne), espacements et alignements, rayons et ombres, icônes et images, comportement aux points de rupture, états.
4. **Mesurer quand la valeur est exacte** : lis la valeur calculée dans le rendu (style calculé du navigateur, inspecteur, valeur du composant) plutôt que de l'estimer sur la capture.
5. **Classer chaque écart** :
   - **bloquant** : élément ou état manquant, texte faux, mise en page cassée à une largeur, contenu coupé ou superposé, accessibilité dégradée (contraste, focus invisible, zone tactile trop petite) ;
   - **mineur** : écart sur une valeur *exacte* de la spécification (couleur, taille, espacement) ;
   - **toléré** : écart sur une valeur *estimée* qui reste dans l'esprit de la maquette, ou différence due aux données.
6. **Attribuer** chaque écart bloquant ou mineur à l'agent qui doit corriger.
7. **Après correction**, recapturer **tous** les écrans et états de la liste, pas seulement la zone corrigée, et mettre à jour le tableau.

## Livrable
```markdown
### Fidélité au design : <écran> (<date>, commit <sha>)
Largeurs : 375, 768, 1280 | États : nominal, vide, erreur | Captures : tests/e2e/captures/accueil/
| Écran / zone | Attendu (source) | Obtenu (capture) | Gravité | Agent |
|--------------|------------------|------------------|---------|-------|
| Accueil / bouton principal | #1E5EFF, rayon 8 (exact, S2) | #2563EB, rayon 4 | mineur | nextjs-implementer |
| Accueil / état vide | message + illustration (spec) | absent | bloquant | nextjs-implementer |
Non vérifié : Android (émulateur indisponible).
```

## Vérifications
- Chaque ligne cite la source de l'attendu et le chemin de la capture.
- Toutes les largeurs et tous les états spécifiés sont capturés, ou listés en non vérifié avec la raison.

## Limites
- Pas de correction pendant la revue quand tu es `e2e-validator` : tu signales, l'agent d'implémentation corrige.
- Une comparaison automatique pixel par pixel ne remplace pas la lecture zone par zone.

## En cas de blocage
- Spécification d'écran absente : appliquer d'abord le skill `design-inputs`, ou demander à `ui-ux-designer`.
- Écart dû à une source ambiguë ou contradictoire : appliquer la règle du skill `design-inputs` (source la plus récente, sinon la plus détaillée), classer l'écart « toléré » et consigner l'hypothèse.
