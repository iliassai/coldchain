# Cold Chain

Application Django pour le projet IoT **Cold Chain** : recevoir les mesures de température et d’humidité d’un capteur DHT11 relié à un ESP8266, les enregistrer dans SQLite et les consulter par API ou dans un tableau de bord.

## Fonctionnement

```text
DHT11 → ESP8266/NodeMCU → Wi-Fi → API REST Django → SQLite → tableau de bord
```

- `DHT/models.py` définit une mesure avec `temp`, `hum` et la date `dt`.
- `DHT/serializers.py` convertit les mesures en JSON et valide les données reçues.
- `DHT/api.py` fournit les vues de lecture et d’enregistrement, avec des alertes e-mail et Telegram facultatives lorsque leurs paramètres sont configurés.
- `DHT/templates/DHT/dashboard.html` affiche la dernière mesure.
- `projet/` contient la configuration Django.

## Prérequis sous Linux

- Git
- Python compatible avec les versions indiquées dans `requirements.txt`

### Option utilisée par ce dépôt : mise + uv

Le fichier `mise.toml` sélectionne Python `3.15.2` et configure automatiquement l’environnement `.venv`. Depuis la racine du dépôt :

```bash
mise install
mise exec -- uv pip install -r requirements.txt
```

`_.python.venv = { path = ".venv", create = true }` demande à mise de créer `.venv` s’il n’existe pas, puis de l’activer dans les shells initialisés avec mise et dans `mise exec`. uv installe les dépendances dans cet environnement. Il n’est pas nécessaire de lancer `uv venv` séparément.

### Option standard : Python `venv` + pip

Si tu ne veux pas utiliser mise, crée l’environnement avec Python et installe les mêmes dépendances avec pip :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Cette option utilise le Python système (`python3`) au lieu de la version sélectionnée dans `mise.toml`.

### Autre option : uv sans mise

Si Python et uv sont déjà installés, uv peut créer l’environnement et installer les dépendances :

```bash
uv venv --python python3 .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
```

Ces méthodes sont alternatives : choisis-en une seule pour créer l’environnement et installer les dépendances.

## Configuration locale

Copier le modèle de variables d’environnement et le modifier localement :

```bash
cp .env.example .env
```

Le secret Django de développement fourni dans `.env.example` est uniquement un exemple local. Remplacez-le par une valeur aléatoire avant tout partage ou déploiement (par exemple avec `python -c 'import secrets; print(secrets.token_urlsafe(50))'`). Le fichier `.env` est ignoré par Git. Les paramètres Gmail et Telegram sont facultatifs ; laissez-les vides pour désactiver ces notifications.

Charger les variables dans le terminal courant puis initialiser SQLite :

```bash
set -a
source .env
set +a
python manage.py migrate
```

Créer un compte d’administration si nécessaire :

```bash
python manage.py createsuperuser
```

## Démarrer le serveur

Pour un accès depuis l’ordinateur uniquement :

```bash
python manage.py runserver
```

Pour recevoir les mesures d’un ESP8266 sur le même réseau Wi-Fi, définir `DJANGO_ALLOWED_HOSTS` avec l’adresse IP locale du PC (par exemple `192.168.1.20`) dans `.env`, puis redémarrer Django en écoutant sur le réseau :

```bash
python manage.py runserver 0.0.0.0:8000
```

Autorisez le port 8000 dans le pare-feu Linux uniquement sur le réseau local de confiance, si nécessaire. Le PC et l’ESP8266 doivent être connectés au même réseau. Dans le programme ESP8266, utiliser l’adresse IP du PC, jamais `localhost` ou `127.0.0.1`.

## Routes de l’application

| Méthode | Adresse | Utilité |
| --- | --- | --- |
| GET | `http://127.0.0.1:8000/api/get` | Récupérer les mesures, sous la clé JSON `data` |
| POST | `http://127.0.0.1:8000/api/post` | Enregistrer une mesure |
| GET | `http://127.0.0.1:8000/dashboard/` | Afficher le tableau de bord |
| GET | `http://127.0.0.1:8000/admin/` | Ouvrir l’administration Django |

Exemple de contenu JSON pour le POST, conforme aux noms de champs utilisés dans ce dépôt :

```json
{"temp": 24.5, "hum": 54.0}
```

La date `dt` est ajoutée automatiquement par Django. Une création réussie renvoie le code HTTP `201`. Pour une requête depuis l’ESP8266, remplacer `127.0.0.1` par l’adresse IP du PC. Les chemins actuels sont `/api/get` et `/api/post` (sans slash final) ; les exemples du tutoriel qui utilisent `/list/`, `/post/`, `temperature` et `humidity` correspondent à une autre version de l’API.

## Vérification

```bash
python manage.py check
python manage.py showmigrations
```

La base `db.sqlite3` est créée localement lors de `migrate` et n’est pas destinée à être versionnée. Les dépendances Python sont décrites dans `requirements.txt`.

## Sécurité

- Ne pas committer `.env`, la base locale ou des identifiants Wi-Fi, e-mail, Telegram et API.
- Les notifications e-mail et Telegram ne fonctionnent que si leurs variables sont configurées.
- `runserver` est le serveur de développement Django ; ne pas l’exposer à Internet ni l’utiliser en production.
- Le dépôt contient actuellement des secrets dans un ancien commit Git. Le retrait du code ne supprime pas les valeurs de l’historique : révoquez/renouvelez immédiatement le mot de passe d’application Gmail et le jeton Telegram, puis nettoyez l’historique avant de publier ou partager le dépôt.
