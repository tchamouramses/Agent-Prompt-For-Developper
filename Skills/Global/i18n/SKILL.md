---
name: i18n
description: Internationaliser une application multilingue sans texte oublié - situer les langues et l'outillage, aucune chaîne visible en dur (interface, attributs, messages du back, e-mails, notifications), clés stables, messages complets avec pluriels ICU, dates, nombres et devises formatés selon la langue, choix et persistance de la langue, RTL, puis contrôle automatique des clés manquantes, des variables et des textes en dur. À utiliser pour toute tâche qui ajoute ou modifie un texte affiché dans un projet multilingue, pour ajouter une langue, ou pour vérifier une livraison multilingue.
---

# Internationalisation (i18n)

`product-analyst` fixe les langues dans `docs/spec.md` ; `ui-ux-designer` écrit les textes et prévoit leur longueur ; l'agent du framework les implémente avec l'outil de la stack (section « Internationalisation » des skills `angular`, `react`, `nextjs`, `expo`, `laravel`, `symfony`, `spring-boot`) ; `code-reviewer`, `e2e-validator` et `quality-gatekeeper` vérifient. Ce skill donne les règles communes à toutes les stacks et la façon de **prouver** qu'aucun texte n'est resté non traduit.

## Quand l'utiliser
- Le projet est multilingue : `docs/spec.md` liste plus d'une langue, ou le code contient déjà des fichiers de traduction (`lang/`, `translations/`, `messages_*.properties`, `locales/`, `messages/`, `i18n/`) ou une librairie de traduction.
- Une tâche ajoute ou modifie un texte visible : écran, composant, message d'erreur ou de validation, e-mail, notification, PDF, export, métadonnées de page.
- Une langue est ajoutée, ou la spec annonce d'autres langues plus tard (préparer l'i18n coûte peu au début et cher après coup).
- Revue ou validation d'une livraison multilingue.

## Ce que l'agent rate sans ce skill
- Il laisse du texte en dur hors du contenu principal : `placeholder`, `alt`, `aria-label`, `title`, notifications et toasts, messages de confirmation, libellés de graphiques, onglet du navigateur, e-mails, messages d'erreur renvoyés par le back.
- Il ajoute la clé dans la langue de référence seulement, ou la recopie telle quelle dans les autres langues.
- Il assemble une phrase par morceaux (`t('vous_avez') + n + t('messages')`) ou gère le pluriel par `n > 1 ? … : …`, faux dans beaucoup de langues (le polonais, l'arabe ou le russe ont plus de deux formes ; le français met le singulier à 0).
- Il formate une date ou un montant à la main (`dd/MM/yyyy`, `toFixed(2) + ' €'`) ou avec la locale de la machine.
- Il fabrique des clés dynamiques (`t('status.' + status)`) que les outils d'extraction ne voient pas, et une valeur ajoutée côté back reste sans traduction.
- Il stocke un libellé traduit en base au lieu d'un code, ou renvoie depuis l'API une phrase en dur au lieu d'un code d'erreur traduisible.
- Il oublie la langue dans la clé de cache ou le rendu serveur, et un utilisateur reçoit la page dans la langue d'un autre, ou l'hydratation échoue.
- Il fixe la largeur d'un bouton sur le texte de la langue de référence : la traduction allemande ou finnoise déborde.
- Il écrit `margin-left` ou une icône de flèche fixe dans une application qui vise une langue de droite à gauche.

## Entrées
- `docs/spec.md` (section « Langues » : langues visées, langue par défaut, régions et devises), `docs/PROJECT.md`, `docs/decisions/` (choix d'outillage déjà fait).
- La configuration i18n et les fichiers de traduction existants, la librairie installée et sa version, les composants voisins.
- Les spécifications d'écran (`docs/ux/ecrans/`) pour les textes exacts.

## Procédure

### 1. Situer le projet
1. **Langues** : lis la section « Langues » de `docs/spec.md`. Absente : déduis-les du code (fichiers de traduction présents) ; sinon le projet est monolingue dans la langue de la spec, noté comme hypothèse (skill `autonomy-policy`).
2. **Monolingue sans langue prévue** : n'installe pas d'outillage i18n (pas de code sans besoin) ; écris quand même les textes dans un seul endroit par écran plutôt que dispersés dans la logique. Les étapes suivantes ne s'appliquent pas, sauf les formats de l'étape 5 (dates et montants restent formatés selon la langue de l'application).
3. **Multilingue ou langue prévue** : note la langue de référence (celle dans laquelle les textes sont écrits en premier, en général la langue par défaut), la langue de repli, le format et l'emplacement des fichiers, la convention de nommage des clés, et ce qui est traduit côté back (validation, e-mails) ou côté front.

### 2. Outillage
1. Réutilise ce qui est installé. Sinon, prends l'outil natif ou de référence de la stack (tableau ci-dessous, détails dans le skill du framework) selon la règle 4 des principes communs, sans demander : consigne le choix et ses raisons dans une ADR (skill `adr`), car il structure tout le front.

| Stack | Outil par défaut | Alternative et quand la choisir |
|-------|------------------|---------------------------------|
| Angular | `@angular/localize` (traduction à la compilation, un build par langue) | Transloco si la langue doit changer sans rechargement ni build séparé |
| React (SPA, Vite) | `react-i18next` | `react-intl` (FormatJS) si le projet l'utilise déjà |
| Next.js (App Router) | `next-intl` | — |
| Expo / React Native | `expo-localization` + `i18next` et `react-i18next` | — |
| Laravel | traduction native (`__()`, `trans_choice()`, `lang/`) | — |
| Symfony | composant Translation (`|trans`, `TranslatorInterface`, `translations/`, format ICU) | — |
| Spring Boot | `MessageSource` (`messages_<langue>.properties`) et `LocaleResolver` | — |

2. Un seul mécanisme par application : pas de deuxième librairie de traduction à côté de la première.

### 3. Clés et fichiers
1. **Clés sémantiques et regroupées par fonctionnalité** : `checkout.summary.title`, `auth.errors.invalid_credentials`. Jamais le texte comme clé dans un projet qui utilise des clés, jamais une même clé réutilisée pour deux contextes différents (« Fermer » une modale et « Fermer » un compte se traduisent différemment).
2. **Clés statiques** : la clé apparaît en entier dans le code pour que l'extraction et la recherche la trouvent. Une valeur venue des données (statut, catégorie) passe par une table de correspondance exhaustive (`{ draft: 'order.status.draft', paid: 'order.status.paid' }`) typée sur l'énumération, pas par une concaténation.
3. **Toutes les langues dans le même changement** : chaque clé ajoutée, modifiée ou supprimée l'est dans tous les fichiers de langue. Une traduction écrite par l'agent est marquée dans le compte rendu « à relire par un locuteur natif » ; elle n'est pas laissée vide ni recopiée de la langue de référence.
4. **Contexte pour le traducteur** quand le mot est ambigu ou court : description ou commentaire selon le format (`@@id` et `meaning|description` pour Angular, `<note>` en XLIFF, commentaire dans le fichier sinon).
5. Une clé supprimée du code est supprimée de tous les fichiers (principes de code, zéro code mort) ; avant de renommer une clé, cherche ses usages en chaîne (skill `change-impact-analysis`).

### 4. Aucun texte visible en dur
Passe chaque surface touchée par la tâche :
- **Interface** : contenu, boutons, liens, titres, `placeholder`, `alt`, `aria-label`, `title`, info-bulles, états vides, chargement et erreur, notifications, confirmations, libellés de graphiques et de tableaux, titre de page et métadonnées.
- **Back** : messages de validation (règles du framework et messages personnalisés), exceptions affichées, e-mails (objet compris), SMS et notifications, PDF et exports (en-têtes de colonnes), libellés d'énumérations exposés.
- **Contrat front et back** : l'API renvoie un **code** stable et ses paramètres (`{ "code": "order.not_payable", "params": { "status": "shipped" } }`, skill `api-contracts`) que le front traduit, ou bien le back traduit selon `Accept-Language` ; un seul des deux modes par projet, consigné. En base, on stocke des codes, pas des libellés traduits ; un contenu saisi par les utilisateurs et multilingue (fiche produit) relève du modèle de données (table de traductions ou colonne JSON par langue), décidé avec `data-modeler`.
- **Exceptions admises** : noms propres et marques, unités normalisées formatées par l'outil, contenu technique destiné aux développeurs (journaux, messages de log, qui restent en une langue).

### 5. Messages, pluriels et formats
1. **Phrase entière avec variables** : `"cart.summary": "{count, plural, =0 {Panier vide} one {# article} other {# articles}} pour {total}"`. L'ordre des mots change selon la langue : jamais de concaténation, jamais de majuscule ou de ponctuation ajoutée par le code.
2. **Pluriels et genres par la syntaxe ICU** (`plural`, `select`) ou le mécanisme du framework (`trans_choice`, `_one`/`_other` d'i18next, `ChoiceFormat`) ; teste au moins 0, 1, 2 et 5, et les formes `few`/`many` si une langue concernée en a.
3. **HTML et liens dans un texte** : mécanisme de texte enrichi de l'outil (`<Trans>` d'i18next, `t.rich` de next-intl, interpolation de balises), jamais `innerHTML` avec du texte traduit non assaini.
4. **Dates, heures, nombres, montants, listes, temps relatif, tri** : API de l'outil ou `Intl` avec la langue active (`Intl.DateTimeFormat`, `Intl.NumberFormat` avec `style: 'currency'` et la devise venant des données, `Intl.RelativeTimeFormat`, `Intl.ListFormat`, `Intl.Collator` pour trier des chaînes) ; côté serveur : `Carbon::translatedFormat()` et `Number::currency()` (Laravel 11+), `IntlDateFormatter` et `NumberFormatter` (PHP intl), `DateTimeFormatter.ofLocalizedDate()` et `NumberFormat.getCurrencyInstance(locale)` (Java). Stockage et échanges en UTC et ISO 8601, conversion au fuseau de l'utilisateur à l'affichage.
5. **Longueur** : prévois 30 à 40 % de texte en plus (davantage pour les textes très courts) ; pas de largeur fixe sur un conteneur de texte, troncature avec texte complet accessible.

### 6. Choix et persistance de la langue
1. Ordre de résolution par défaut : choix explicite de l'utilisateur (profil, cookie) ; segment d'URL pour un site public indexé (`/fr/…`, skill `seo-technique` pour `hreflang`) ; `Accept-Language` ou langue de l'appareil ; langue par défaut.
2. Le choix est persisté et relu au démarrage ; changer de langue met à jour `<html lang>` et `dir` (web) et le titre de page.
3. Rendu serveur : la langue est résolue côté serveur et fait partie de la clé de cache (skill `caching`) ; le client hydrate avec les mêmes messages.
4. Clé manquante à l'exécution : affichage dans la langue de repli, jamais la clé brute ni une chaîne vide, et journalisation de la clé manquante en développement et en test.

### 7. Langues de droite à gauche (si la spec en vise une : arabe, hébreu, persan, ourdou)
- `dir="rtl"` sur `<html>` selon la langue ; CSS en propriétés logiques (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `text-align: start`) ; icônes directionnelles (flèches, retour) inversées, les autres non.
- React Native : `I18nManager.allowRTL(true)` et `I18nManager.forceRTL()` selon la langue, avec redémarrage de l'application (`Updates.reloadAsync()` sous Expo) ; styles en `start`/`end`.
- Les nombres, numéros de téléphone et extraits de code restent de gauche à droite (`<bdi>` ou `dir="ltr"` localement).

### 8. Contrôles automatiques
Intègre au projet ceux que la stack permet (CI comprise, skill `ci-github-actions`), sinon lance-les à la main sur la tâche :
1. **Parité des clés entre langues** : outil de la stack (skill du framework) ou script fourni avec ce skill, pour JSON, YAML et `.properties` (clés manquantes ou en trop, valeurs vides, variables différentes ; valeurs identiques à la référence en avertissement) :
   ```bash
   python3 <dossier du skill i18n>/scripts/verifier-cles.py src/locales/fr.json src/locales/en.json src/locales/ar.json
   ```
   Tableaux PHP de Laravel : convertis chaque fichier en JSON avant (`php -r 'echo json_encode(require "lang/fr/validation.php");'`). Si le projet accepte un script, copie-le dans `scripts/` et branche-le en CI.
2. **Textes en dur** : règle de lint quand elle existe pour la stack (`i18next/no-literal-string` d'`eslint-plugin-i18next` pour React, Next.js et Expo ; `@angular-eslint/template/i18n` avec `@angular/localize`), activée au minimum sur les fichiers modifiés. Sinon, recherche sur le diff des textes entre balises et des attributs textuels :
   ```bash
   git diff -U0 origin/main -- '*.html' '*.tsx' '*.jsx' '*.vue' '*.twig' '*.blade.php' \
     | grep -E '^\+' | grep -E '>[[:space:]]*[[:alpha:]][^<{]*<|(placeholder|alt|title|aria-label)="[^"{]*[[:alpha:]]'
   ```
   Chaque résultat est traduit ou justifié (exception de l'étape 4).
3. **Clés utilisées absentes des fichiers, et clés orphelines** : extraction de l'outil (`ng extract-i18n`, `transloco-keys-manager find`, `i18next-parser`, `debug:translation`) ou, à défaut, recherche des appels de traduction du diff et vérification de chaque clé dans le fichier de référence.
4. **Typage** quand l'outil le permet (messages typés de `next-intl`, Transloco ou i18next avec déclaration des ressources) : une clé inexistante casse la compilation.

### 9. Tests
- Un test de composant ou de vue rendu dans **deux langues**, dont une autre que la langue de référence, qui vérifie un texte traduit et un format (date ou montant).
- Les pluriels testés aux valeurs de l'étape 5.
- e2e (`e2e-validator`) : au moins un parcours critique rejoué dans une deuxième langue, captures à l'appui ; la langue RTL si elle est visée (miroir de la mise en page, focus, icônes) ; changement de langue et persistance après rechargement.
- Pseudo-localisation si l'outil la propose (textes allongés et accentués) pour repérer les débordements et les textes non extraits.

## Livrable
Le code et les fichiers de traduction de toutes les langues, et ce bloc dans le compte rendu (et l'entrée de journal, skill `project-docs-tracking`) :
```markdown
## i18n — <tâche>
Langues : fr (référence), en, ar (RTL) · Outil : next-intl 4.x (ADR-0007)
Clés : 12 ajoutées, 2 supprimées, dans les 3 langues · Traductions en, ar : à relire par un locuteur natif
Parité : `python3 …/verifier-cles.py messages/fr.json messages/en.json messages/ar.json` → 0 erreur, 1 avertissement (cart.ok identique, voulu)
Textes en dur : `npx eslint --rule … src/app/checkout` → 0 · Tests : rendu fr et ar ✔, pluriels 0/1/2/5 ✔
Non vérifié : relecture native de l'arabe
```

## Vérifications
- Aucune clé manquante, en trop ou vide dans une langue, et aucune variable différente (commande citée, résultat exact).
- Aucun texte visible en dur dans le diff, ou chaque exception justifiée.
- Pluriels, dates et montants passent par l'outil ou `Intl`, avec la langue active.
- Un test au moins rend la fonctionnalité dans une deuxième langue.

## Limites
- La qualité linguistique des traductions produites par un agent n'est pas garantie : elles sont livrées complètes, marquées « à relire », et la relecture native reste une réserve, pas un blocage.
- Les textes à portée juridique (conditions générales, mentions légales, consentements) ne sont pas traduits par l'agent pour publication : leur version dans chaque langue est une décision humaine (règle 5 des principes communs) ; l'agent prépare les clés et un brouillon marqué comme tel.
- La traduction de contenus saisis par les utilisateurs (traduction automatique, workflow de traduction) est une fonctionnalité à part entière, spécifiée par `product-analyst`.

## En cas de blocage
- Langue demandée sans fichier existant : crée le fichier depuis la langue de référence, traduis toutes les clés et signale-le.
- Outil d'extraction ou de lint impossible à lancer : script de parité et recherche sur le diff, et l'outil manquant noté en réserve avec une tâche au plan.
- Texte en dur dans du code que la tâche ne touche pas : ne l'élargis pas ; liste-le en dette dans le compte rendu.
