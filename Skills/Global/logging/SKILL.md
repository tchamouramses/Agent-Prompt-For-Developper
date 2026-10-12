---
name: logging
description: Écrire des journaux applicatifs exploitables - structurés (message fixe et contexte en champs), au bon niveau, corrélés par identifiant de requête et de trace jusque dans les tâches asynchrones, sans donnée personnelle ni secret. À utiliser pour ajouter ou revoir des logs dans du code, pour diagnostiquer un bug à partir des journaux, et pour configurer le format et les niveaux par environnement (Laravel, Symfony, Spring Boot, Next.js, Angular, Expo).
---

# Journalisation

Les secrets ne sont jamais écrits nulle part (règle 5 des principes communs) et les erreurs ne sont jamais avalées en silence (principes des agents qui modifient du code, « Typage et erreurs »). Ce skill dit quoi journaliser, comment, et ce qui ne doit jamais l'être.

## Quand l'utiliser
- `implementer` et agents de framework : code qui traite une erreur, un appel externe, une tâche planifiée ou en file, une action métier sensible (paiement, droits, suppression).
- `debugger` : lecture des journaux pour reproduire, ajout de journaux de diagnostic temporaires.
- Configuration du format et des niveaux de journalisation d'un projet.

## Ce que l'agent rate sans ce skill
- Il interpole les valeurs dans le message (`"Commande $id payée par $email"`) : impossible à filtrer ou agréger, et l'e-mail part dans les journaux.
- Il journalise `$e->getMessage()` seul : la trace et l'exception d'origine (« Caused by ») sont perdues.
- Il journalise puis relance la même exception à chaque couche : une erreur produit cinq entrées.
- Il écrit `error` pour un cas attendu (identifiant introuvable, validation refusée) et noie les vraies alertes.
- Il journalise un objet entier (requête, modèle, entité, DTO) : en-têtes `Authorization`, mots de passe, jetons et données personnelles sortent avec.
- Il perd la corrélation dans les jobs, les écouteurs et les appels sortants : impossible de relier l'entrée de la file à la requête qui l'a créée.
- Il laisse des `console.log`, `dd()`, `dump()`, `System.out.println` de diagnostic dans le diff.

## Entrées
- La configuration existante (`config/logging.php`, `config/packages/monolog.yaml`, `application.yml`, logger déjà utilisé côté JavaScript), le format attendu par l'outil de collecte s'il est connu, la convention des journaux déjà présents dans le code.

## Procédure
1. **Suivre l'existant** : même logger, mêmes noms de champs, même canal. Pas de nouvelle librairie si le framework journalise déjà (règle 4 des principes communs).
2. **Message fixe, contexte en champs** :
   - Laravel : `Log::info('Commande payée', ['order_id' => $order->id]);` ; contexte de requête partagé par `Log::withContext([...])` dans un middleware ;
   - Symfony : `LoggerInterface` injecté, `$logger->info('Commande payée', ['order_id' => $id]);` ; champs communs par un processor Monolog ;
   - Spring Boot : SLF4J, `log.info("Commande payée orderId={}", id);`, champs communs dans le `MDC` ; sortie JSON avec `logging.structured.format.console` (Spring Boot 3.4 et suivants, sinon encodeur Logback du projet) ;
   - Node et Next.js côté serveur : le logger du projet (souvent pino) avec un objet de champs en premier argument.
3. **Choisir le niveau** :

| Niveau | Quand | Exemple |
|--------|-------|---------|
| `error` | une action a échoué et quelqu'un doit agir | paiement refusé par une erreur du fournisseur, job abandonné après ses tentatives |
| `warning` | anomalie gérée, à surveiller si elle se répète | nouvelle tentative d'un appel externe, valeur de configuration par défaut appliquée |
| `info` | événement métier ou technique notable, peu fréquent | commande créée, job terminé avec ses compteurs |
| `debug` | diagnostic, désactivé en production | valeurs intermédiaires, requête construite |

   Un 404, une validation refusée ou un accès refusé attendu ne sont pas des `error` ; un refus d'accès se trace en `warning` ou `info` pour l'audit (skill `owasp-checklist`).
4. **Journaliser l'exception, pas son message** : `Log::error('…', ['exception' => $e])`, `$logger->error('…', ['exception' => $e])`, `log.error("… orderId={}", id, e)` (l'exception en dernier argument). Une exception est journalisée une seule fois, là où elle est traitée ; ailleurs, on la propage (skill `error-handling`).
5. **Corréler** : identifiant de requête lu dans `X-Request-Id` (ou généré) et renvoyé dans la réponse, `traceparent` si OpenTelemetry est en place ; même identifiant transmis aux appels HTTP sortants et passé dans la charge utile des jobs, puis remis dans le contexte du worker.
6. **Exclure les données sensibles** : jamais de mot de passe, jeton, clé, cookie, en-tête `Authorization`, numéro de carte, contenu de `.env` ; pas d'e-mail, téléphone, adresse ni nom quand un identifiant interne suffit ; pas de corps de requête ou de réponse complet. Liste blanche de champs plutôt que masquage après coup ; paramètres sensibles marqués `#[\SensitiveParameter]` en PHP 8.2+ pour les traces.
7. **Volume** : pas de journal dans une boucle sur des milliers d'éléments ; un résumé avec compteurs en fin de traitement.
8. **Front et mobile** (Angular, Next.js client, Expo) : pas de `console.log` en production ; erreurs remontées par le gestionnaire global ou l'outil de suivi déjà présent, sans jeton ni donnée du formulaire.
9. **Diagnostic temporaire** (`debugger`) : préfixe repérable (`[diag]`), niveau `debug`, retiré avant de rendre : `rg -n "\[diag\]|console\.log|dd\(|dump\(|System\.out\.print" <fichiers touchés>`.

## Livrable
Le code journalisé, et dans le compte rendu :
```markdown
**Journaux** : <événement> — niveau <niveau> — champs <liste> — fichier:ligne
**Corrélation** : <identifiant et propagation (requête, job, appel sortant)>
**Exclus volontairement** : <champs sensibles non journalisés>
```

## Vérifications
- Un test vérifie le journal d'un cas d'erreur important : `Log::shouldReceive('error')` (Laravel), `TestHandler` de Monolog (Symfony), `OutputCaptureExtension` (Spring Boot).
- `rg -n -i "password|token|secret|authorization" <fichiers touchés>` ne montre aucune valeur sensible passée à un logger.
- Aucun journal de diagnostic dans le diff.

## Limites
- Le choix et la mise en place d'un outil de collecte ou de suivi d'erreurs hébergé est une infrastructure ou un service tiers : décision humaine préparée (règle 5).
- La durée de conservation des journaux contenant des données personnelles est un choix de conformité : à signaler, pas à décider.
- Les journaux de production se lisent seulement si l'accès est fourni, en lecture seule.

## En cas de blocage
- Format de collecte inconnu : JSON sur la sortie standard en production, texte lisible en local ; hypothèse consignée.
- Pas de mécanisme de corrélation dans le projet : ajoute le middleware d'identifiant de requête dans le périmètre de la tâche, ou une tâche du plan s'il touche toute l'application.
