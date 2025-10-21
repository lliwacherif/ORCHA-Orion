# Conventions de Nommage des Projets et Branches GitLab

Ce document décrit les conventions de nommage pour les projets et les branches au sein des dépôts GitLab. Ces conventions visent à améliorer l'organisation du code, à faciliter la collaboration et à garantir une communication claire.


## Nommage des Branches

Les branches sont utilisées pour isoler le travail de développement et suivre les modifications. Utilisez des préfixes pour identifier clairement l'objectif de la branche et faire référence aux tâches liées dans OpenProject.

* **Format :** `prefix/numéro-de-tâche_nom-de-tâche`
    * `prefix` : Identifie l'objectif de la branche (voir la liste des préfixes de branches ci-dessous).
    * `numéro-de-tâche` : Numéro de référence pour la tâche liée dans OpenProject (ex. : T-456).
    * `nom-de-tâche` : Une brève description de la tâche.

**Exemple :** `feature/T-456_authentification-utilisateur` (branche de fonctionnalité pour la tâche T-456, implémentation de l'authentification utilisateur).

## Liste des Préfixes de Branches

* `feature/` : Utilisé pour le développement de nouvelles fonctionnalités.
* `bugfix/` : Utilisé pour corriger des bugs dans le code.
* `hotfix/` : Utilisé pour des corrections critiques directement depuis la branche de production.
* `release/` : Utilisé pour préparer une nouvelle version.
* `docs/` : Utilisé pour les modifications de la documentation.

## Liste des Préfixes de Messages de Commit

Les messages de commit doivent décrire clairement les modifications apportées. Utilisez des préfixes pour catégoriser le type de changement.

* `feat` : Ajoute ou supprime une nouvelle fonctionnalité.
* `fix` : Corrige un bug.
* `refactor` : Restructure le code sans changer le comportement.
* `perf` : Améliore les performances.
* `style` : Modifications de formatage (espaces, indentation, etc.).
* `test` : Ajoute ou corrige des tests.
* `docs` : Modifications de la documentation.
* `build` : Changements des outils de construction, des pipelines CI, des dépendances ou de la version du projet.
* `ops` : Changements opérationnels (infrastructure, déploiement, sauvegarde, etc.).
* `chore` : Changements divers (ex. : modification de `.gitignore`).

**Exemples de Messages de Commit :**

* `feat: ajouter des notifications par e-mail pour les nouveaux messages directs`
* `fix(caddie) : empêcher la commande d'un caddie vide`
* `refactor : implémenter le calcul du nombre de Fibonacci en utilisant la récursion`
* `style : supprimer la ligne vide`

**Notes Supplémentaires :**

* Pour les changements importants, incluez une explication claire dans le message de commit et utilisez le suffixe `!` après le préfixe (ex. : `feat!: supprimer l'endpoint de liste de billets`).
* Fournissez une brève explication pour les corrections de bugs (`fix : ajouter un paramètre manquant à l'appel de service. L'erreur est survenue à cause de <raisons>`) et pour les améliorations de performance (`perf : réduire l'empreinte mémoire pour déterminer les visiteurs uniques en utilisant HyperLogLog`).

En suivant ces conventions, nous pouvons maintenir un environnement GitLab propre, organisé et collaboratif.