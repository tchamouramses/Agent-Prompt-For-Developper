---
name: seo-technique
description: Mettre en place et vérifier le référencement technique d'un site public - rendu serveur ou statique, métadonnées par page (title, description, canonique, robots, Open Graph), sitemap.xml, robots.txt, vrais codes HTTP (404, 301), hreflang, données structurées JSON-LD, Core Web Vitals (LCP, INP, CLS) ; implémentation en Next.js, Angular SSR, Laravel, Symfony et vérification par curl et Lighthouse. À utiliser pour implémenter ou auditer les pages publiques d'un site, préparer une refonte ou relire les exigences de docs/seo/.
---

# SEO technique

`seo-specialist` fixe les exigences par page (`docs/seo/pages.md`) et audite ; l'agent du framework les implémente sur les pages publiques. Ce skill dit comment les implémenter sans piège et comment prouver qu'un robot voit ce qu'on croit lui montrer.

## Quand l'utiliser
- `nextjs-implementer`, `angular-implementer`, agents Laravel ou Symfony : création ou modification d'une page publique, d'une route, d'une redirection.
- `seo-specialist` : exigences techniques (étape 5) et audit avant livraison (étapes 8 et 9).

## Ce que l'agent rate sans ce skill
- Il croit qu'un `Disallow` dans `robots.txt` retire une page de l'index : il empêche seulement l'exploration, et le robot ne voit alors plus le `noindex` de la page.
- Il laisse partir en production le `noindex` ou l'en-tête `X-Robots-Tag` de la pré-production, ou l'inverse : la pré-production indexée.
- Il renvoie une page « introuvable » avec un code 200 (soft 404), typique d'une application rendue côté client.
- Il met la même `title`, la même description ou une canonique vers l'accueil sur toutes les pages ; il fait pointer la canonique des pages 2, 3… d'une liste vers la page 1.
- Il met dans `sitemap.xml` des URL redirigées, en `noindex` ou non canoniques, et une `lastmod` égale à la date du build pour toutes.
- Il génère le contenu ou les métadonnées côté client et conclut « ça s'affiche » après l'avoir vu dans un navigateur, sans lire le HTML brut.
- Il écrit des `hreflang` sans réciprocité ni auto-référence.
- Il charge en différé l'image principale du haut de page (LCP dégradé) et omet les dimensions des images (CLS).
- Il prend le score Lighthouse pour les Core Web Vitals : c'est une mesure de laboratoire, et INP ne s'y mesure pas.

## Entrées
- `docs/seo/strategie.md` et `docs/seo/pages.md` s'ils existent, la liste des routes publiques, le framework et sa version (skill `version-compatibility`), l'URL de production prévue, la configuration des environnements, et pour une refonte la table ancienne URL → nouvelle URL.

## Procédure
1. **Rendu** : chaque page publique est rendue côté serveur ou générée statiquement, contenu principal et métadonnées compris. Pages privées (compte, panier, administration) : `noindex` et hors sitemap.
2. **Métadonnées par page**, depuis `docs/seo/pages.md` : `title` unique, description unique, un seul `h1`, canonique absolue vers l'URL exacte de la page (protocole, domaine, barre finale cohérents), `robots` seulement quand il diffère du défaut, Open Graph (`og:title`, `og:description`, `og:image` absolue, `og:url`).
   - **Next.js (App Router)** : `metadataBase` dans le layout racine, `export const metadata` ou `generateMetadata` par page avec `alternates.canonical` ; `app/sitemap.ts` et `app/robots.ts` (types `MetadataRoute`) ; `notFound()` pour un vrai 404.
   - **Angular** : `ng add @angular/ssr`, pré-rendu des routes statiques selon la version ; services `Title` et `Meta` dans chaque route ; canonique par un `<link>` ajouté via `DOCUMENT` ; vrai 404 côté serveur avec le mécanisme de la version installée ; sitemap généré au build ou par une route serveur.
   - **Laravel, Symfony** : section `head` du layout Blade ou Twig alimentée par chaque contrôleur ; `abort(404)` ou `NotFoundHttpException` ; sitemap par une route qui renvoie `application/xml`.
3. **Codes HTTP** : 404 pour une ressource absente, 410 pour une ressource retirée définitivement, 301 directe (sans chaîne) pour une URL déplacée ; une seule forme d'URL servie (HTTPS, avec ou sans `www`, barre finale), les autres redirigées en 301.
4. **robots.txt et sitemap** : `robots.txt` à la racine avec la ligne `Sitemap: <URL absolue>`, qui ne bloque ni CSS ni JS ; sitemap avec uniquement les URL canoniques, indexables et en 200 ; `lastmod` = dernière modification réelle du contenu ; au-delà de 50 000 URL ou 50 Mo, un index de sitemaps.
5. **Environnements** : en dehors de la production, `X-Robots-Tag: noindex` par variable d'environnement, jamais codé en dur ; en production, vérifier qu'il est absent.
6. **Multilingue** : une URL par langue, `hreflang` réciproques avec auto-référence et `x-default` ; Next.js : `alternates.languages`.
7. **Données structurées** en JSON-LD, du type prévu par `docs/seo/pages.md` (Organization, LocalBusiness, Product, Article, BreadcrumbList), cohérentes avec le contenu visible. Next.js : `<script type="application/ld+json">` avec `JSON.stringify(data).replace(/</g, '\\u003c')` pour éviter l'injection. Les résultats enrichis FAQ et HowTo ne sont plus affichés pour la plupart des sites : ne pas les promettre.
8. **Core Web Vitals** (au 75e centile des visites réelles : LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1) : image LCP non différée et chargée en priorité, dimensions sur toute image et tout encart, polices auto-hébergées avec `font-display` adapté (`next/font` en Next.js), JavaScript client réduit sur les pages publiques. Le détail des optimisations relève de `performance-optimizer`.
9. **Vérifier sur le build de production lancé en local** (`next build && next start`, `ng build` puis le serveur SSR, ou le serveur PHP) :
   ```bash
   U=http://localhost:3000
   curl -s "$U/page" | grep -oiE '<title>[^<]*</title>|<h1[^>]*>|<link[^>]+rel="canonical"[^>]*>|<meta[^>]+name="(description|robots)"[^>]*>'
   curl -sI "$U/page" | grep -iE '^(HTTP|x-robots-tag|location)'
   curl -s -o /dev/null -w '%{http_code}\n' "$U/page-qui-n-existe-pas"     # attendu : 404
   curl -s "$U/sitemap.xml" | grep -oE '<loc>[^<]+</loc>' | sed -E 's#</?loc>##g; s#^https?://[^/]+##' \
     | while read -r p; do printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$U$p")" "$p"; done | grep -v '^200'
   npx lighthouse "$U/page" --only-categories=performance,seo --output=json --output-path=./lh-mobile.json --chrome-flags="--headless"
   npx lighthouse "$U/page" --only-categories=performance,seo --preset=desktop --output=json --output-path=./lh-desktop.json --chrome-flags="--headless"
   ```
   Le HTML brut (`curl`, sans JavaScript) doit contenir le contenu principal et les métadonnées. Données structurées : validateur schema.org ou test des résultats enrichis, en collant le code pour une page locale. Lighthouse donne LCP, CLS et TBT (indicateur de laboratoire proche d'INP) ; les valeurs réelles viennent des données de terrain, à défaut **non vérifiées**.

## Livrable
Le code des pages et, dans le compte rendu ou l'audit `docs/seo/audit-AAAA-MM-JJ.md` :
```markdown
| Page | HTTP | title | description | h1 | canonique | robots | sitemap | JSON-LD | LCP / CLS / TBT (mobile) |
|------|------|-------|-------------|----|-----------|--------|---------|---------|--------------------------|
| /tarifs | 200 | ✔ 54 car. | ✔ 152 car. | 1 | ✔ absolue | défaut | ✔ | Product ✔ | 1,9 s / 0,02 / 120 ms |
Redirections : <n> testées, 0 chaîne · Soft 404 : non · noindex hors production : ✔ via `<variable>`
```

## Vérifications
- Chaque commande de l'étape 9 lancée sur le build de production, sortie citée ; aucune URL du sitemap hors 200.
- Une URL inexistante renvoie 404 ; aucune page publique ne dépend du JavaScript client pour son contenu principal ou ses métadonnées.
- La configuration de production ne contient aucun `noindex` global.

## Limites
- Soumission du sitemap, Search Console et outils payants passent par un compte tiers : action réservée (règle 5 des principes communs), préparée pour l'humain.
- Les mesures de laboratoire ne remplacent pas les données de terrain ; aucune promesse de positionnement.

## En cas de blocage
- Page publique impossible à rendre côté serveur dans l'architecture actuelle : implémente le reste (métadonnées, codes HTTP, sitemap), marque le rendu **non conforme** et escalade à `architect`.
- URL de production inconnue : place-la dans une variable d'environnement avec une valeur de développement, consigne l'hypothèse et liste-la dans le compte rendu.
