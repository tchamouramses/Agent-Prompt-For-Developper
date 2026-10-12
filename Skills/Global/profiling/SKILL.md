---
name: profiling
description: Mesurer avant d'optimiser - définir une métrique et un scénario reproductibles, mesurer dans des conditions proches de la production, localiser le goulot avec le profileur adapté à la stack (Laravel, Symfony, Spring Boot, Angular, Next.js, Expo/React Native, base de données), puis re-mesurer dans les mêmes conditions. À utiliser pour toute lenteur, consommation mémoire, taille de bundle ou fluidité insuffisante, avant et après chaque optimisation.
---

# Profilage

`performance-optimizer` n'optimise rien sans mesure et annule un changement sans gain significatif. Ce skill donne la façon de mesurer pour que ces chiffres soient fiables. Rien ne se profile en production sans accord humain (règle 5 des principes communs).

## Quand l'utiliser
- `performance-optimizer` : étapes « définir la mesure », « mesurer l'état initial », « identifier le goulot » et « re-mesurer ».
- `debugger` : quand le comportement est correct mais lent (le skill `debugging-method` s'arrête là).
- Tout agent qui affirme qu'un changement « améliore les performances ».

## Ce que l'agent rate sans ce skill
- Il mesure en mode développement : `next dev`, build Angular de développement, `APP_DEBUG=true`, Xdebug actif, Debugbar chargée, application React Native en debug. Les chiffres n'ont rien à voir avec la production.
- Il mesure une seule fois, cache froid puis cache chaud mélangés, et conclut sur du bruit.
- Il teste avec 10 lignes en base : le N+1 et l'index manquant restent invisibles.
- Il optimise ce qu'il soupçonne au lieu de ce que le profileur montre, souvent une fonction qui pèse 2 % du temps.
- Il compare avant et après dans des conditions différentes (autre jeu de données, autre machine, profileur actif d'un seul côté).
- Il écrit un micro-benchmark d'une fonction isolée et en déduit le gain sur la requête entière.

## Entrées
- Le symptôme : quoi est lent, où, pour qui, depuis quand ; l'objectif chiffré s'il existe (spec, critère d'acceptation).
- Les outils déjà installés dans le projet (`composer.json`, `package.json`, `pom.xml`), le moteur de base et sa version.

## Procédure
1. **Écrire la mesure** avant de toucher au code : métrique (p50 et p95 du temps de réponse, nombre de requêtes SQL, mémoire de pointe, taille de bundle compressé, LCP, images par seconde), scénario exact (route, paramètres, utilisateur, volume de données), objectif. Sans objectif fourni, prends une pratique courante (par exemple p95 < 500 ms pour une page serveur, LCP < 2,5 s) et consigne-la comme hypothèse.
2. **Préparer des conditions proches de la production** sur la machine locale ou de test :
   - Laravel : `APP_DEBUG=false`, `php artisan optimize`, OPcache actif, Xdebug désactivé hors séance de profilage ;
   - Symfony : `APP_ENV=prod`, `bin/console cache:warmup --env=prod` ;
   - Spring Boot : jar construit (`./mvnw package` ou `./gradlew bootJar`), JVM échauffée par quelques passages avant de mesurer ;
   - Angular : `ng build` (configuration production) servi statiquement ; Next.js : `next build && next start` ;
   - Expo/React Native : build release (`npx expo run:android --variant release`, `npx expo run:ios --configuration Release`) sur un appareil réel ou un émulateur, jamais l'application de développement.
3. **Données réalistes** : volume généré par les factories ou seeders à l'échelle attendue (au moins des milliers de lignes sur les tables touchées), jamais une copie de données réelles (règle 5).
4. **Mesurer plusieurs fois** : au moins 5 passages après échauffement, médiane et p95 notés. Requête HTTP : `curl -o /dev/null -s -w "%{time_total}\n" <url>` en boucle, ou l'outil de charge déjà présent (`k6`, `hey`, `ab`) contre la machine locale uniquement.
5. **Localiser le goulot** avec l'outil de la couche :

| Couche | Outils |
|--------|--------|
| Laravel | Debugbar ou Telescope s'ils sont présents ; `DB::listen` ou `DB::enableQueryLog()` pour compter les requêtes ; `Model::preventLazyLoading()` en test pour révéler les N+1 ; Xdebug (`XDEBUG_MODE=profile`) |
| Symfony | Web Profiler (onglets Performance et Doctrine) ; composant `Stopwatch` autour d'un bloc suspect |
| Spring Boot | Actuator `/actuator/metrics/http.server.requests` ; JDK Flight Recorder (`java -XX:StartFlightRecording=duration=60s,filename=rec.jfr -jar app.jar`, lu dans JDK Mission Control) ; `spring.jpa.properties.hibernate.generate_statistics=true` pour compter les requêtes |
| Base de données | `EXPLAIN ANALYZE` (PostgreSQL, MySQL 8.0.18+), journal des requêtes lentes ; méthode dans le skill `db-query-optimization` |
| Angular | `ng build --stats-json` puis analyse du fichier de statistiques ; Angular DevTools (profileur) ; Lighthouse |
| Next.js | tailles affichées par `next build` ; `@next/bundle-analyzer` s'il est présent ; React DevTools Profiler ; Lighthouse sur `next start` |
| Expo/React Native | moniteur de performance intégré (images par seconde JS et UI) ; React DevTools Profiler ; profilage Hermes |

6. **Classer** les contributions : la plus grosse part du temps ou de la mémoire est le goulot à traiter, une seule à la fois. Un poste sous 10 % du total ne justifie pas d'optimisation.
7. **Re-mesurer** après le changement, mêmes conditions, même nombre de passages. Un gain inférieur à la variation entre passages n'est pas un gain : le changement est annulé.

## Livrable
```markdown
**Scénario** : <route ou écran, données, conditions (build, cache, machine)>
| Métrique | Avant (médiane / p95) | Après (médiane / p95) | Gain | Passages |
|----------|-----------------------|-----------------------|------|----------|
| Temps de réponse | 840 / 1 210 ms | 190 / 260 ms | -77 % | 10 |
| Requêtes SQL | 203 | 4 | -199 | 1 |
**Goulot** : <fichier:ligne, part du total, outil qui le montre>
**Non vérifié** : <conditions de production non reproduites>
```

## Vérifications
- Les commandes de mesure et leurs sorties sont citées (skill `evidence-tracking`), avant et après.
- Les deux mesures ont les mêmes conditions, écrites dans le livrable.
- Aucun outil de profilage (Xdebug, `generate_statistics`, `Stopwatch`, compteur temporaire) ne reste actif dans la configuration ni dans le diff.

## Limites
- Profilage, test de charge ou activation d'un agent APM sur la production ou un environnement partagé : décision humaine préparée (règle 5). Un profileur payant aussi (règle 4).
- Une mesure locale ne reproduit ni le réseau, ni la concurrence, ni le cache de production : dis-le dans « Non vérifié ».

## En cas de blocage
- Aucun profileur installé : commence par les compteurs gratuits du framework (requêtes, temps par étape) ; un outil de développement gratuit peut être ajouté selon la règle 4, en dépendance de développement.
- Lenteur non reproduite localement : livre la mesure locale, les hypothèses classées et ce qu'il faudrait observer en production (journal de requêtes lentes, métrique Actuator, trace).
