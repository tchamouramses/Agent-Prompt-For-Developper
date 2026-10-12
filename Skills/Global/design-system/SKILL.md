---
name: design-system
description: Définir, étendre et tenir un design system - jetons en trois niveaux (primitifs, sémantiques, composants), échelles d'espacement et de typographie, couleurs aux contrastes vérifiés, thème sombre, composants avec variantes et états, correspondance exacte entre docs/ux/design-system.md et le code (variables CSS, thème Tailwind, thème Angular, objet de thème React Native). À utiliser pour créer ou compléter docs/ux/design-system.md, ajouter un composant ou un jeton, ou repérer les valeurs codées en dur.
---

# Design system

`ui-ux-designer` produit `docs/ux/design-system.md` (procédure de conception, étape 6, et extraction depuis les sources, étape 3) ; les agents qui codent une interface réutilisent ses composants et jetons (principes des agents qui modifient du code, « Interfaces et sources visuelles »). Ce skill dit comment le structurer pour qu'il reste cohérent et applicable.

## Quand l'utiliser
- `ui-ux-designer` : création, extraction depuis des sources (skill `design-inputs`) ou extension du design system.
- Agents qui codent une interface : avant d'ajouter une couleur, un espacement ou un composant qui semble manquer.

## Ce que l'agent rate sans ce skill
- Il crée des quasi-doublons : `#1E5EFF` et `#1F5FFF`, espacements de 15, 16 et 18 px, trois boutons qui diffèrent d'un pixel.
- Il nomme les jetons par leur valeur (`blue-500`, `space-16`) et les utilise directement dans les composants : le thème sombre ou un changement de marque oblige à tout reprendre.
- Il code les valeurs en dur dans les composants alors que le jeton existe.
- Il spécifie un composant à l'état par défaut seulement : ni survol, ni focus visible, ni désactivé, ni erreur, ni chargement.
- Il retire le contour de focus (`outline: none`) sans le remplacer.
- Il crée un composant neuf au lieu d'ajouter une variante à l'existant, ou l'inverse : un composant à vingt options.
- Il laisse diverger la documentation et le code : le document dit 8 px, le thème dit 10 px.

## Entrées
- `docs/ux/design-system.md` s'il existe, les sources visuelles et leurs spécifications (`docs/ux/sources.md`, `docs/ux/ecrans/`), le thème déjà présent dans le code (variables CSS, configuration Tailwind, thème de la librairie de composants, fichier de thème mobile), la librairie de composants installée.

## Procédure
1. **Inventorier l'existant** dans le code avant de créer quoi que ce soit : fichier de jetons ou de thème, composants partagés, et valeurs codées en dur :
   ```bash
   rg -n --glob '!**/{tokens,theme}*' '#[0-9a-fA-F]{3,8}\b|rgba?\(' src app
   rg -n '\b[0-9]+px\b' --glob '*.{css,scss}' src
   ```
2. **Structurer les jetons en trois niveaux** :
   - **primitifs** : la palette et les échelles brutes (`color.blue.600`, `space.4`), jamais utilisés directement par un composant ;
   - **sémantiques** : le rôle (`color.text.default`, `color.bg.surface`, `color.action.primary`, `color.feedback.error`, `space.inline.md`) ; c'est le niveau que les composants consomment et que le thème sombre redéfinit ;
   - **composants**, seulement si nécessaire : `button.primary.bg` qui pointe vers un jeton sémantique.
3. **Fixer les échelles** :
   - espacement sur une base de 4 ou 8 (4, 8, 12, 16, 24, 32, 48, 64) ;
   - typographie limitée à 6 à 8 tailles, avec hauteur de ligne et graisse associées, en unités relatives sur le web (`rem`) pour suivre le réglage de taille du navigateur ;
   - rayons, ombres, durées d'animation et points de rupture en quelques valeurs nommées.
   Une valeur extraite d'une source qui tombe à 1 ou 2 px d'un cran de l'échelle prend la valeur du cran ; l'écart est noté dans la spécification d'écran.
4. **Couleurs** : pour chaque paire texte et fond, et chaque composant non textuel (bordure de champ, icône seule, focus) contre son fond, calcule le contraste et note-le (seuils et calcul : skill `accessibility`). Une couleur de marque trop claire pour du texte reste réservée aux aplats ; une variante foncée est créée pour le texte. Les états de retour (erreur, succès, avertissement) ont toujours une icône ou un texte en plus de la couleur.
5. **Thème sombre**, s'il est prévu : redéfinir uniquement les jetons sémantiques ; contrôler les contrastes à nouveau, ne pas inverser mécaniquement la palette.
6. **Spécifier chaque composant** : rôle, anatomie, variantes (principal, secondaire, danger), tailles, états (repos, survol, focus visible, actif, désactivé, chargement, erreur), contenu long, comportement clavier ou tactile, jetons utilisés, quand ne pas l'utiliser. Avant d'en créer un, vérifie si une variante d'un existant suffit ; au-delà de quelques variantes sans lien, découpe.
7. **Relier au code** sans écart, avec la convention déjà en place :
   - web : variables CSS sur `:root` et sur le sélecteur du thème sombre ; avec Tailwind, le thème du projet selon sa version installée (skill `version-compatibility`) ;
   - Angular avec une librairie de composants : son système de thème, pas de surcharge de ses classes internes ;
   - React Native et Expo : un objet de thème typé unique consommé par `StyleSheet.create`, `useColorScheme()` pour le thème système ;
   - un seul fichier source des jetons ; la documentation cite son chemin.
8. **Versionner** : ajout, renommage ou suppression de jeton noté dans le document (section « Historique ») ; un jeton renommé garde un alias jusqu'à la tâche de nettoyage du plan.

## Livrable
`docs/ux/design-system.md` :
```markdown
# Design system
Source des jetons dans le code : `<chemin>` · Librairie de composants : <nom et version, ou aucune>
## Jetons sémantiques
| Jeton | Clair | Sombre | Usage | Contraste |
|-------|-------|--------|-------|-----------|
| color.text.default | gray.900 | gray.50 | texte courant | 15,8:1 sur bg.surface |
## Échelles (espacement, typographie, rayons, ombres, points de rupture)
## Composants
### Bouton
Variantes : primary, secondary, danger · Tailles : sm, md · États : repos, survol, focus, actif, désactivé, chargement
Jetons : … · Ne pas utiliser pour : navigation (utiliser Lien)
## Historique
```

## Vérifications
- Aucune valeur codée en dur nouvelle dans le diff (commandes de l'étape 1 relancées sur les fichiers modifiés).
- Chaque jeton documenté existe dans le fichier source du code avec la même valeur, et inversement.
- Chaque composant documente ses états, dont le focus visible ; chaque paire de couleurs utilisée a son contraste noté.

## Limites
- Une identité visuelle à créer de zéro alors que l'entreprise en a peut-être une reste une décision humaine à revoir (rôle `ui-ux-designer`) : applique une direction neutre et consigne-la.
- Une librairie de composants payante ou sous licence restrictive est une action réservée (règle 4 des principes communs).

## En cas de blocage
- Deux sources donnent des valeurs différentes pour le même rôle : retiens la plus fiable selon le skill `design-inputs`, crée un seul jeton et note l'écart.
- Le code existant mélange plusieurs systèmes de styles : n'en ajoute pas un nouveau ; documente celui qui domine et ajoute la convergence au plan.
