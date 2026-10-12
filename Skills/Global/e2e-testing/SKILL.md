---
name: e2e-testing
description: Écrire et faire tourner des tests de bout en bout fiables sur l'application lancée - Playwright pour le web, Maestro pour le mobile (Expo, React Native) - avec sélecteurs accessibles, assertions qui attendent, données isolées par test, connexion réutilisée, services tiers simulés côté serveur, traces et captures, et chasse aux tests intermittents. À utiliser pour valider un parcours utilisateur, ajouter des tests e2e à la CI ou réparer un test e2e instable.
---

# Tests de bout en bout

L'agent `e2e-validator` choisit les scénarios et rédige le rapport. Ce skill dit comment écrire et exécuter les tests pour qu'ils soient fiables et rejouables par la CI.

## Quand l'utiliser
- `e2e-validator` : tout parcours à valider sur l'application lancée.
- `test-engineer` : ajout des quelques parcours critiques à la suite (skill `testing-strategy`).
- `devops-engineer` : exécution des tests e2e dans la CI.
- Tout agent face à un test e2e rouge ou intermittent.

## Ce que l'agent rate sans ce skill
- Il attend avec `waitForTimeout` ou `sleep`, ou il teste `isVisible()` sans attendre : le test passe ou échoue selon la vitesse de la machine.
- Il cible des classes CSS ou des chemins XPath qui changent au moindre ajustement de style.
- Il se connecte par l'interface au début de chaque test, ce qui rend la suite lente et fragile.
- Ses tests partagent des données : le deuxième échoue si le premier n'a pas tourné, ou si un autre test a déjà créé le même e-mail.
- Il simule toute l'API du back dans le navigateur : le test passe, mais il ne vérifie plus l'intégration.
- Il intercepte dans le navigateur un appel à un service tiers que le serveur fait lui-même : l'interception n'a aucun effet et le test appelle le vrai service.
- Il active les nouvelles tentatives automatiques et considère vert un test qui n'a réussi qu'au deuxième essai.

## Entrées
- Les scénarios dérivés des critères d'acceptation, les commandes de lancement de l'application, l'outil e2e déjà présent (`playwright.config.*`, dossier `.maestro/`, Cypress, Dusk, Panther), les seeds ou factories.

## Procédure
1. **Garder l'outil en place** s'il existe. Sinon, installe le standard (règle 4 des principes communs) : Playwright pour le web, quel que soit le back ; Maestro pour une application Expo ou React Native. Consigne le choix.
2. **Lancer l'application comme en vrai**, sur une base dédiée aux tests, jamais celle de développement partagée ni la production :
   - Playwright démarre le serveur avec `webServer` (`command`, `url`, `reuseExistingServer: !process.env.CI`) ;
   - la base est préparée avant la suite par la commande du framework, sur l'environnement de test, par exemple `php artisan migrate:fresh --seed --env=testing`.
3. **Simuler les services tiers au bon endroit** :
   - un appel fait par le navigateur se simule avec `page.route()` ;
   - un appel fait par le serveur (paiement, e-mail, API tierce) se simule côté serveur : pilote de test du framework, configuration qui pointe vers un faux service local, mode bac à sable du fournisseur.
   - Le back du projet lui-même n'est jamais simulé.
4. **Sélecteurs**, dans cet ordre de préférence : `getByRole(..., { name })`, `getByLabel`, `getByText` pour un contenu stable, `getByTestId`. Ajoute un `data-testid` (web) ou un `testID` (React Native) au code si aucun sélecteur accessible n'existe. N'utilise ni classe CSS ni XPath.
5. **Assertions qui attendent** :
   - `await expect(locator).toBeVisible()`, `toHaveText`, `toHaveURL` ;
   - `expect.poll()` pour une condition hors de la page, par exemple une ligne en base ou un e-mail reçu par le faux service.
   - Jamais d'attente fixe.
6. **Isoler chaque test** :
   - il crée ses propres données, avec des valeurs uniques (e-mail suffixé par un identifiant aléatoire) ;
   - il ne dépend d'aucun autre test ;
   - il passe seul (`npx playwright test <fichier> -g "<nom>"`) et dans n'importe quel ordre.
7. **Réutiliser la connexion** : un projet `setup` se connecte une fois par rôle et enregistre la session (`storageState`) ; les tests l'utilisent. Seul le parcours de connexion lui-même passe par le formulaire.
8. **Couvrir ce qu'un test unitaire ne voit pas** : rechargement de page au milieu du parcours, retour arrière, double clic sur l'envoi, message d'erreur du back affiché à l'écran, accès direct par URL à une page protégée.
9. **Configurer les preuves** : `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`, rapport HTML ; captures et traces jointes au rapport en cas d'échec.
10. **Chasser l'instabilité avant de livrer** : `npx playwright test --repeat-each=10 <fichiers nouveaux ou modifiés>`. Un seul échec sur dix est un test à corriger (skill `debugging-method`). En CI, `retries: 1` sert seulement à obtenir une trace : un test marqué « flaky » compte comme un échec.
11. **Navigateurs et tailles** : au minimum Chromium ; ajoute Firefox, WebKit et un viewport mobile (375 px) pour un site public. Mobile : Android en émulateur, iOS en simulateur si l'environnement le permet, sinon « non vérifié ».

### Mobile avec Maestro
```yaml
appId: com.exemple.app
---
- launchApp:
    clearState: true
- tapOn:
    id: "login-email"        # testID du composant
- inputText: "e2e+${UNIQUE}@example.test"
- tapOn: "Se connecter"
- assertVisible: "Bienvenue"
```
- Lancement : `maestro test -e UNIQUE=$(date +%s) .maestro/`, sur un build de développement ou de prévisualisation installé dans l'émulateur.
- Mêmes règles que pour le web : `testID` stables, données uniques, pas d'attente fixe.
- `extendedWaitUntil` sert pour une condition longue.

## Livrable
- Les fichiers de test, la configuration et les données de test, rejouables par une seule commande citée.
- Pour chaque exécution : commande, navigateurs ou appareils, résultat (réussis, échoués, instables), chemin du rapport, traces et captures des échecs.

## Vérifications
- Aucun `waitForTimeout`, `sleep` ni sélecteur CSS ou XPath dans les tests ajoutés (recherche citée).
- Les nouveaux tests ont passé `--repeat-each=10` sans échec, ou leur instabilité est rapportée comme échec.
- Aucun appel réseau vers un service tiers réel pendant l'exécution.
- La commande de la CI lance bien ces tests.

## Limites
- Peu de tests e2e : seulement les parcours critiques. Les règles métier se testent plus bas (skill `testing-strategy`).
- La comparaison visuelle avec le design suit le skill `design-fidelity-review`, pas des captures de référence générées par le test lui-même.
- Jamais contre la production ni avec des comptes ou paiements réels (règle 5 des principes communs).

## En cas de blocage
- L'application ne démarre pas en environnement de test : rapporte la commande et l'erreur, et renvoie le problème à `devops-engineer`. Ne remplace pas le back par des simulations pour avancer.
- Pas d'émulateur ni de navigateur disponible : écris quand même les tests, valide leur syntaxe (`npx playwright test --list` pour le web), et marque l'exécution « non vérifiée ».
- Service tiers sans mode de test ni moyen de le simuler côté serveur : marque le parcours « non vérifié », explique pourquoi, et propose l'interface de simulation à ajouter au plan.
