# Module superadmin

Créer le premier compte depuis le dossier du projet :

```powershell
python -m flask --app app create-superadmin superadmin
```

La commande demande le nom complet et le mot de passe avec confirmation, sans afficher le mot de passe. Choisir un identifiant inexistant. Se connecter ensuite dans l'interface habituelle : le panneau Administration apparaît au-dessus du parcours.

Le superadmin peut consulter les comptes et leurs statistiques (modules réussis, nombre de quiz et d'examens, moyenne des scores), rechercher, créer, renommer, désactiver, réactiver ou supprimer un compte, attribuer ou retirer le rôle superadmin et réinitialiser les mots de passe.

La suppression efface définitivement les résultats et demande confirmation. Le superadmin ne peut ni supprimer ou désactiver son propre compte, ni retirer son propre rôle. Une réinitialisation ou une désactivation invalide les sessions existantes. Les mots de passe restent hachés et ne sont jamais renvoyés dans les statistiques. Le nouveau mot de passe est choisi dans le panneau puis transmis personnellement à l'utilisateur.

Les comptes existants restent utilisables avec le rôle utilisateur par défaut. Aucun compte superadmin ni mot de passe par défaut n'est créé automatiquement.

Pour un déploiement avec plusieurs processus, définir `SECRET_KEY` avec une valeur aléatoire persistante commune aux processus. Sans cette variable, la clé change à chaque démarrage et les sessions sont déconnectées. Le stockage JSON actuel est adapté à une seule instance/processus ; son verrou ne coordonne pas plusieurs processus.

Validation : `python -m unittest discover -s tests -v`.
