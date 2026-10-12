---
name: accessibility
description: Concevoir, implémenter et vérifier une interface conforme WCAG 2.2 niveau AA, sur le web et en React Native - sémantique, clavier et focus, libellés, contrastes calculés, zones tactiles, formulaires et erreurs, contenus dynamiques, lecteurs d'écran ; contrôles automatiques avec axe (Playwright, jest-axe), Lighthouse et les règles ESLint d'accessibilité, puis contrôles manuels ciblés. À utiliser pour spécifier l'accessibilité d'un écran, coder un composant interactif, auditer une page avant livraison ou interpréter un score Lighthouse.
---

# Accessibilité

`ui-ux-designer` intègre l'accessibilité à chaque écran et vérifie les contrastes ; `seo-specialist` relève le score d'accessibilité dans son audit. La cible par défaut est **WCAG 2.2 niveau AA** ; un niveau imposé par la spec ou une obligation légale l'emporte. Ce skill donne les exigences qui comptent, leur vérification et les limites des outils.

## Quand l'utiliser
- `ui-ux-designer` : section « Accessibilité » de chaque `docs/ux/ecrans/<écran>.md`, contrastes du design system.
- `seo-specialist`, `e2e-validator`, agents qui codent une interface : audit d'une page ou d'un écran, composant interactif (menu, onglets, modale, liste déroulante, carrousel).

## Ce que l'agent rate sans ce skill
- Il déclare la page accessible parce que Lighthouse affiche 100 ou qu'axe ne trouve rien : les outils automatiques ne détectent qu'une partie des défauts (ordre de focus, pertinence d'un libellé, piège clavier leur échappent).
- Il fabrique un bouton avec un `div` cliquable, ou ajoute des rôles ARIA par-dessus un élément natif qui les avait déjà.
- Il retire le contour de focus, ou laisse un en-tête collant masquer l'élément qui a le focus (2.4.11, nouveau en 2.2).
- Il estime un contraste à l'œil au lieu de le calculer, et oublie les éléments non textuels (bordure de champ, icône seule, 3:1).
- Il donne à une icône seule un libellé vide, ou un `alt` de décoration à une image qui porte de l'information.
- Il signale une erreur par la seule couleur rouge, sans texte relié au champ.
- Il désactive l'agrandissement du texte (`maximum-scale=1`, `allowFontScaling={false}`) pour protéger la mise en page.
- En React Native, il oublie `accessibilityRole` et `accessibilityState`, et un `Pressable` est lu « bouton » sans nom ou pas lu du tout.

## Entrées
- La spécification d'écran ou l'écran implémenté, le design system, l'application lancée en local ou en test, la cible (web, mobile), le niveau exigé par `docs/spec.md`.

## Procédure
1. **Sémantique d'abord** : élément natif quand il existe (`button`, `a href`, `label`, `input`, `select`, `nav`, `main`, `h1`-`h6` dans l'ordre) ; ARIA seulement pour un widget sans équivalent natif, en suivant le pattern correspondant du guide WAI-ARIA Authoring Practices (rôle, états, clavier). Une langue de page (`lang`), un titre de page unique par vue.
2. **Clavier et focus** : tout ce qui se fait à la souris se fait au clavier ; ordre de focus égal à l'ordre de lecture ; focus toujours visible et non masqué ; lien d'évitement vers le contenu ; modale qui enferme le focus et le rend à l'origine ; aucun piège ; changement de route qui déplace le focus ou annonce le nouveau titre.
3. **Libellés et alternatives** : chaque champ a un libellé associé ; chaque bouton ou lien a un nom explicite hors contexte (pas « Cliquez ici ») ; icône seule → nom accessible ; image informative → `alt` qui dit l'information, image décorative → `alt=""`.
4. **Contrastes, calculés** : texte 4,5:1, grand texte (24 px, ou 18,66 px en gras) 3:1, composants et graphiques 3:1. Calcul sans dépendance :
   ```bash
   python3 -c 'import sys;L=lambda h:(lambda c:0.2126*c[0]+0.7152*c[1]+0.0722*c[2])([x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in (int(h[i:i+2],16)/255 for i in (0,2,4))]);a,b=sorted((L(x.lstrip("#")) for x in sys.argv[1:3]),reverse=True);print(round((a+0.05)/(b+0.05),2))' 1E5EFF FFFFFF   # → 5.12
   ```
5. **Tailles et adaptation** : zones cliquables d'au moins 24 × 24 px CSS (2.5.8) et, sur mobile, 44 × 44 pt (iOS) ou 48 × 48 dp (Android) selon les conventions des plateformes ; contenu utilisable à 320 px de large sans défilement horizontal et avec un texte agrandi à 200 % ; aucune information portée par la seule couleur ; alternative à tout glissement (2.5.7) ; animations réduites si `prefers-reduced-motion`.
6. **Formulaires et erreurs** : erreur en texte, reliée au champ (`aria-describedby`, `aria-invalid`), annoncée ; pas de ressaisie d'une information déjà donnée dans le même parcours (3.3.7) ; authentification sans test cognitif, coller et gestionnaire de mots de passe autorisés (3.3.8).
7. **Contenus dynamiques** : message de statut annoncé (`role="status"` ou `aria-live="polite"`, `role="alert"` pour une erreur) ; chargement signalé ; pas de délai imposé sans moyen de le prolonger.
8. **React Native et Expo** : `accessibilityRole`, `accessibilityLabel`, `accessibilityHint` si l'action n'est pas évidente, `accessibilityState` (`disabled`, `selected`, `checked`, `expanded`) ; `accessible` pour regrouper une carte en un seul élément lu ; `hitSlop` pour agrandir une petite cible ; texte qui suit la taille système (ne pas désactiver `allowFontScaling`, borner avec `maxFontSizeMultiplier` si la mise en page casse) ; `AccessibilityInfo.announceForAccessibility` pour un changement non visible.
9. **Contrôles automatiques**, intégrés aux tests quand l'outil est déjà présent ou ajouté selon la règle 4 des principes communs :
   - parcours web (Playwright, `@axe-core/playwright`) :
     ```ts
     const { violations } = await new AxeBuilder({ page })
       .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
     expect(violations).toEqual([]);
     ```
   - composants (Jest ou Vitest, `jest-axe`) : `expect(await axe(container)).toHaveNoViolations()` ;
   - lint : `eslint-plugin-jsx-a11y` (React, Next.js), règles d'accessibilité des modèles de `angular-eslint` (Angular) ;
   - page complète : `npx lighthouse <url> --only-categories=accessibility --output=json --output-path=./lighthouse-a11y.json --chrome-flags="--headless"` ;
   - React Native : requêtes par rôle et nom de Testing Library (`getByRole('button', { name: 'Envoyer' })`) ; un test qui ne trouve pas l'élément par son rôle révèle un défaut.
10. **Contrôles manuels ciblés**, sur chaque écran modifié : parcours complet au clavier seul (Playwright `page.keyboard.press('Tab')` et vérification de l'élément actif), zoom 200 % et largeur 320 px, lecture du nom de chaque contrôle dans l'arbre d'accessibilité (`await page.locator('main').ariaSnapshot()` depuis Playwright 1.49, ou les outils du navigateur). Lecteur d'écran réel (NVDA, VoiceOver, TalkBack) : fais-le si l'environnement le permet, sinon marque-le **non vérifié**.

## Livrable
En conception, la section « Accessibilité » de `docs/ux/ecrans/<écran>.md` ; en audit, ce bloc dans le rapport de l'agent (`docs/seo/audit-AAAA-MM-JJ.md`, rapport e2e ou compte rendu) :
```markdown
## Accessibilité (WCAG 2.2 AA) — <écran>, <date>
Automatique : axe <n> violation(s) [commande] · Lighthouse accessibilité <score> [commande]
| Critère | Élément | Constat | Gravité | Correction | Agent |
|---------|---------|---------|---------|------------|-------|
| 1.4.3 Contraste | bouton secondaire | 3,1:1 (attendu 4,5:1) | bloquant | jeton color.action.secondary plus foncé | ui-ux-designer |
Manuel : clavier ✔ · zoom 200 % ✔ · 320 px ✔ · lecteur d'écran non vérifié (aucun disponible)
```

## Vérifications
- Commandes automatiques citées avec leur résultat exact ; chaque contraste noté est calculé, pas estimé.
- Le parcours clavier de chaque écran modifié est décrit pas à pas.
- Aucun « conforme » sans les contrôles manuels ; ce qui n'a pas été testé est listé.

## Limites
- Ce skill ne délivre pas de déclaration de conformité légale : une obligation réglementaire d'accessibilité et la déclaration publique qui l'accompagne sont des choix à portée légale (règle 5 des principes communs).
- Un score Lighthouse ne prouve rien seul ; il complète axe et les contrôles manuels.

## En cas de blocage
- Composant d'une librairie non accessible et impossible à corriger proprement : contourne au plus près (libellé, rôle ajouté par l'API publique du composant), note le défaut amont et ajoute le remplacement au plan.
- Contraste imposé par une maquette finale insuffisant : implémente la variante conforme la plus proche, signale-le à `ui-ux-designer` et consigne l'écart.
