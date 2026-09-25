# Cap Citoyenneté 🍁

Application locale Flask de préparation à l’examen de citoyenneté canadienne.

## Démarrage

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
python generate_questions.py
python app.py
```

Ouvrir ensuite `http://127.0.0.1:5000`.

## Fonctions

- comptes locaux avec mots de passe hachés;
- 10 modules et banque JSON de 300 questions;
- parcours séquentiel avec déverrouillage à 75 %;
- accès libre à n’importe quel module depuis le tableau de bord;
- correction immédiate et explication après chaque réponse;
- examens blancs aléatoires de 20 questions avec minuterie de 45 minutes;
- historique, meilleurs scores et interface responsive;
- aucune base de données : les résultats sont conservés dans `data/users.json`.

## Important

Le contenu est un outil d’entraînement non officiel. Toujours réviser le guide officiel **Découvrir le Canada**. Les fonctions ou titulaires politiques susceptibles de changer doivent être vérifiés avant l’examen.
