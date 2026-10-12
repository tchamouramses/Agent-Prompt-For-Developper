---
name: security-java
description: Sécuriser du code Java et Spring Boot - contrôle d'accès sur la ressource avec Spring Security, entrées validées, injections JPQL et SQL, désérialisation Jackson, XML, appels sortants, Actuator, secrets et audit des dépendances Maven ou Gradle. À utiliser pour écrire, relire ou auditer du code Java exposé à des entrées externes.
---

# Sécurité Java

La liste générale des risques est dans le skill `owasp-checklist`. Ce skill dit où ils se cachent dans un projet Java et Spring, et comment les fermer.

## Quand l'utiliser
- Écrire ou modifier une route, un DTO d'entrée, une requête, un appel sortant, un traitement de fichier ou de XML.
- Revue de sécurité ou audit d'un projet Java (`security-auditor`, `code-reviewer`).

## Ce que l'agent rate sans ce skill
- Il protège la route par rôle (`hasRole('USER')`) mais pas la ressource : un utilisateur lit la commande d'un autre en changeant l'identifiant.
- Il désactive CSRF pour faire passer un test, dans une application à session.
- Il concatène un paramètre dans une requête JPQL, native ou un `ORDER BY`.
- Il active le typage polymorphe de Jackson sur une donnée externe (exécution de code à la désérialisation).
- Il parse du XML externe avec les réglages par défaut (XXE).
- Il expose Actuator (`exposure.include=*`) ou les traces d'erreur.

## Entrées
- `SecurityFilterChain` et configuration de sécurité, contrôleurs et DTO touchés, `application*.yml`, dépendances.

## Procédure
1. **Contrôle d'accès, pour chaque route touchée** :
   - règle d'URL dans la chaîne de filtres (`authorizeHttpRequests`), avec `anyRequest().authenticated()` ou `denyAll()` en dernier ;
   - autorisation sur la ressource : vérification du propriétaire ou du tenant dans le service, ou `@PreAuthorize("@autorisations.peutLire(#id, authentication)")` avec `@EnableMethodSecurity` ;
   - listes et recherches filtrées dans la requête par propriétaire ou tenant ;
   - un test par refus attendu (skill `testing-java`).
2. **Entrées** : DTO dédié validé (`@Valid`, contraintes Bean Validation) ; jamais une entité liée directement à la requête (affectation de champs non prévus, `id`, `role`) ; tailles maximales sur les chaînes et collections ; `spring.servlet.multipart.max-file-size` adapté.
3. **Injections** :
   - JPQL et SQL : paramètres nommés (`:id`) ou méthodes dérivées ; tri et colonnes dynamiques par liste blanche, ou `Sort` construit à partir de propriétés autorisées ;
   - commandes : `ProcessBuilder` avec une liste d'arguments, jamais `Runtime.exec` d'une chaîne construite ;
   - expressions : jamais d'évaluation SpEL ou de script sur une donnée reçue.
4. **Désérialisation et XML** :
   - Jackson : pas de `activateDefaultTyping` ni de `@JsonTypeInfo(use = Id.CLASS)` sur une donnée externe ; types polymorphes par nom logique (`Id.NAME`) et liste fermée ;
   - jamais `ObjectInputStream` sur une donnée externe ;
   - XML : désactiver les DTD et entités externes (`XMLConstants.FEATURE_SECURE_PROCESSING`, `disallow-doctype-decl`) sur `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory`.
5. **Fichiers** : nom généré, chemin normalisé et vérifié sous le dossier prévu (`path.normalize().startsWith(base)`), type vérifié sur le contenu, stockage hors des ressources statiques.
6. **Appels sortants** : URL fournie par l'utilisateur seulement en `https`, hôte résolu et refusé s'il est privé, local ou de métadonnées, sans suivre les redirections vers ces adresses ; délais explicites.
7. **Authentification et session** :
   - mots de passe avec `PasswordEncoderFactories.createDelegatingPasswordEncoder()` ou BCrypt / Argon2 ; jamais de hachage maison ;
   - API à jetons : `spring-boot-starter-oauth2-resource-server` avec vérification de l'émetteur, de l'audience et de l'expiration ; pas de décodage JWT manuel ;
   - CSRF actif pour une application à session ; désactivé seulement pour une API sans état, et consigné ;
   - CORS limité aux origines connues ; limitation de débit sur la connexion et les routes coûteuses.
8. **Configuration et exposition** : Actuator limité (`management.endpoints.web.exposure.include=health,info`) et protégé ; `server.error.include-stacktrace=never` et `include-message=never` en production ; console H2 et devtools absents de la production ; secrets fournis par l'environnement ou un coffre, jamais dans `application.yml` versionné ; journaux sans mot de passe, jeton ni donnée personnelle inutile.
9. **Dépendances** : audit avec l'outil configuré (OWASP Dependency-Check `./mvnw org.owasp:dependency-check-maven:check`, plugin Gradle équivalent, ou l'analyse de dépendances de la plateforme du dépôt) ; une vulnérabilité haute ou critique dans une dépendance utilisée est bloquante.

## Livrable
Pour une implémentation : les protections appliquées et leurs tests, citées dans le compte rendu. Pour une revue ou un audit : chaque constat avec fichier et ligne, scénario d'attaque concret, gravité et correction proposée.

## Vérifications
- Chaque route touchée a au moins un test de refus d'accès.
- Audit des dépendances lancé, résultat cité (ou **non vérifié** avec la raison).
- Recherche lancée et citée sur le diff : `createQuery\(.*\+|createNativeQuery\(.*\+|activateDefaultTyping|Id.CLASS|ObjectInputStream|Runtime.getRuntime\(\).exec|csrf\(.*disable|exposure.include=\*|permitAll`.

## Limites
- Ce skill ne remplace pas un test d'intrusion. Les choix à portée légale (données personnelles, conservation) restent des décisions humaines (règle 5 des principes communs).

## En cas de blocage
- Correction qui casse un contrat consommé hors du dépôt : applique la protection la plus forte compatible et signale le risque restant comme **Bloquant** pour `security-auditor` et `quality-gatekeeper`.
- Vulnérabilité de dépendance sans version corrigée : documente le contournement et le risque résiduel.
