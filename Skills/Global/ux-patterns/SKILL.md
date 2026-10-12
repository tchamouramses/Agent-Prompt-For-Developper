---
name: ux-patterns
description: Choisir et spécifier les patterns d'interface éprouvés - navigation, formulaires et validation, états d'écran (chargement, vide, erreur, succès), actions destructives, listes, recherche et filtres, retours et notifications, modales, conventions mobiles iOS et Android, micro-textes. À utiliser pour concevoir un parcours ou un écran, compléter les états qu'une maquette ne montre pas, ou relire une spécification d'écran avant implémentation.
---

# Patterns d'interface

`ui-ux-designer` définit les étapes de conception (parcours, écrans, états, micro-textes). Ce skill donne le pattern à retenir pour chaque situation courante et les pièges qui produisent une interface jolie mais pénible. L'accessibilité détaillée relève du skill `accessibility`, les jetons et composants du skill `design-system`.

## Quand l'utiliser
- `ui-ux-designer` : procédure de conception (étapes 2 à 9) et complément des états absents d'une source.
- Agents qui codent une interface : un état ou une interaction n'est pas spécifié dans `docs/ux/ecrans/<écran>.md`.

## Ce que l'agent rate sans ce skill
- Il utilise le placeholder comme libellé : il disparaît à la saisie et l'utilisateur ne sait plus ce qu'il remplit.
- Il valide à chaque frappe et affiche « e-mail invalide » dès la première lettre.
- Il désactive le bouton d'envoi tant que le formulaire est invalide, sans dire ce qui manque.
- Il écrit « Une erreur est survenue » au lieu de dire ce qui s'est passé et quoi faire, et met les erreurs dans un toast qui disparaît.
- Il vide le formulaire après une erreur serveur.
- Il ne conçoit que l'état nominal : pas de premier usage vide, pas de liste de 0 ou 10 000 éléments, pas de texte très long.
- Il demande « Êtes-vous sûr ? » pour toute action, ce qui habitue à cliquer « Oui » sans lire.
- Il empile les modales, ou met un parcours de plusieurs étapes dans une modale.
- Il applique les conventions iOS sur Android (ou l'inverse), ou recopie un menu hamburger de bureau sur mobile.

## Entrées
- `docs/spec.md` (stories, règles, rôles), `docs/ux/parcours.md` et `docs/ux/ecrans/` existants, la cible (web, mobile, les deux), les écrans déjà codés du projet pour rester cohérent.

## Procédure
1. **Navigation** : web, navigation principale visible sur bureau (5 à 7 entrées au plus), fil d'Ariane au-delà de 2 niveaux, URL propre à chaque vue partageable (filtres, onglets, pagination dans l'URL) ; mobile, barre d'onglets en bas pour 3 à 5 destinations principales, pile de navigation pour le détail, retour système Android et geste de retour iOS respectés.
2. **Formulaires** :
   - libellé visible au-dessus du champ, aide sous le champ, placeholder seulement pour un exemple ;
   - type de champ adapté (`email`, `tel`, sélecteur de date, clavier numérique mobile), autocomplétion autorisée ;
   - validation au départ du champ (`blur`) puis à chaque frappe une fois l'erreur affichée, et à l'envoi ;
   - bouton d'envoi actif : à l'envoi, focus sur le premier champ en erreur et résumé des erreurs ;
   - message d'erreur à côté du champ, qui dit comment corriger (« 8 caractères minimum, il en manque 3 ») ;
   - saisie conservée après une erreur serveur ; bouton désactivé avec indicateur pendant l'envoi (double soumission).
3. **États de chaque écran** : spécifie systématiquement :
   - **chargement** : rien sous 300 ms environ, puis squelette de la mise en page pour un contenu, indicateur local pour une action ; barre de progression au-delà de quelques secondes ;
   - **vide** : premier usage (explication et action principale), aucun résultat de recherche (rappel des critères et moyen de les élargir), tout traité ;
   - **erreur** : ce qui s'est passé, ce que l'utilisateur peut faire, bouton « Réessayer » si c'est temporaire ; erreur partielle sans bloquer le reste de l'écran ;
   - **succès** : confirmation proportionnée (message en ligne ou redirection vers l'objet créé) ;
   - **limites** : texte long (troncature avec texte complet accessible), nombres et dates localisés, droits insuffisants, hors ligne sur mobile.
4. **Actions destructives** : réversible → exécuter tout de suite et proposer « Annuler » quelques secondes ; irréversible → confirmation qui nomme l'objet et la conséquence (« Supprimer le projet X et ses 12 fichiers »), bouton libellé par le verbe, jamais « OK » ; très grave → saisie du nom de l'objet.
5. **Listes** : pagination pour un contenu qu'on recherche ou partage, chargement progressif pour un flux qu'on parcourt, avec conservation de la position au retour ; tri et filtres visibles avec leur état actif et un moyen de tout réinitialiser ; actions groupées si l'usage le justifie.
6. **Recherche et filtres** : recherche tolérante (casse, accents), résultats mis à jour après une courte pause de saisie ou à la validation, nombre de résultats affiché.
7. **Retours et notifications** : en ligne près de l'action pour une erreur ou un résultat ; toast uniquement pour une confirmation non critique, jamais pour une erreur qui demande une action ; bannière pour un état global (hors ligne, maintenance).
8. **Modales** : réservées à une tâche courte qui interrompt volontairement ; une seule à la fois, fermeture par Échap et par un bouton visible, focus enfermé puis rendu à l'élément d'origine ; un parcours en plusieurs étapes devient une page.
9. **Micro-textes** : verbes d'action sur les boutons (« Créer le devis »), vocabulaire de l'utilisateur et non du code, ton constant, même terme pour la même notion dans tout le produit.
10. **Consigner** chaque pattern retenu qui n'est pas évident dans la spécification d'écran, et les choix récurrents dans `docs/ux/parcours.md` pour que tous les écrans les appliquent.

## Livrable
Dans chaque `docs/ux/ecrans/<écran>.md` :
```markdown
## États
| État | Déclencheur | Contenu affiché | Actions | Source |
|------|-------------|-----------------|---------|--------|
| Chargement | > 300 ms | squelette de 5 lignes | — | proposé, absent de la source |
| Vide (premier usage) | 0 devis | « Aucun devis pour l'instant » + « Créer un devis » | créer | proposé |
| Erreur réseau | échec du chargement | « Impossible de charger les devis. Vérifiez votre connexion. » | Réessayer | proposé |
## Interactions
Validation : au départ du champ puis en direct ; envoi : bouton désactivé + indicateur ; suppression : immédiate + « Annuler » 5 s.
```

## Vérifications
- Chaque écran spécifie chargement, vide, erreur, succès et limites, ou dit pourquoi un état est sans objet.
- Aucun champ sans libellé visible ; aucun message d'erreur générique ; aucune erreur dans un toast.
- Chaque action irréversible a une confirmation qui nomme l'objet ; chaque action réversible a son « Annuler ».

## Limites
- Les conventions du projet existant l'emportent sur ce skill (principes communs, posture senior) ; un écart nuisible est signalé, pas imposé.
- Ce skill ne remplace pas un test avec de vrais utilisateurs : un choix de pattern reste une hypothèse consignée.

## En cas de blocage
- Pattern dépendant d'une règle métier inconnue (annulation possible ou non) : retiens le plus prudent pour les données, consigne-le en hypothèse et signale-le à `product-analyst`.
- Conflit entre la maquette et un pattern de ce skill : garde la maquette si elle fait foi, et signale le problème d'usage dans la spécification d'écran.
