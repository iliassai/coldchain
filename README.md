# Cold Chain

Application Django pour le projet IoT **Cold Chain** : recevoir les mesures de température et d’humidité d’un capteur relié à un ESP8266, les enregistrer dans SQLite et les consulter par API ou dans un tableau de bord.

## Fonctionnement

```text
DHT11 → ESP8266/NodeMCU → Wi-Fi → API REST Django → SQLite → tableau de bord
```

- `monitoring/models.py` définit les réfrigérateurs, capteurs, identifiants capteur, seuils et mesures.
- `monitoring/` authentifie les requêtes capteur et enregistre les mesures de façon idempotente.
- `accounts/` définit le compte utilisateur email et les rôles.
- `DHT/` conserve les anciens chemins API pendant la migration.
- `firmware/esp8266-dht11/` contient le sketch ESP8266, sans secrets versionnés.
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

Le secret Django de développement fourni dans `.env.example` est uniquement un exemple local. Remplacez-le par une valeur aléatoire avant tout partage ou déploiement (par exemple avec `python -c 'import secrets; print(secrets.token_urlsafe(50))'`). Le fichier `.env` est ignoré par Git. Les variables Gmail et Telegram sont conservées pour une future intégration; cette première fondation n’envoie pas encore de notifications.

La configuration utilise `db-v2.sqlite3`. L’ancienne base `db.sqlite3` est conservée telle quelle car elle contient l’historique du prototype et a déjà appliqué les migrations Django avec le modèle utilisateur par défaut. Ne pointez pas la nouvelle version vers cette ancienne base : le changement vers `AUTH_USER_MODEL` nécessite une base fraîche ou un plan de migration de données explicite. Les mesures de l’ancienne table `Dht11` ne sont pas automatiquement copiées dans le nouveau modèle `Measurement`.

Charger les variables dans le terminal courant puis initialiser la nouvelle base SQLite :

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
| POST | `http://127.0.0.1:8000/api/v1/ingest/measurements/` | Enregistrer une mesure avec `external_id`, `temperature`, `humidity` et `measured_at` |
| POST | `http://127.0.0.1:8000/api/post` | Adaptateur legacy : corps `temp`/`hum`, même service sécurisé |
| GET | `http://127.0.0.1:8000/api/get` | Lire les anciennes mesures de la table `Dht11` au format `temp`/`hum`/`dt` |
| GET | `http://127.0.0.1:8000/dashboard/` | Afficher le tableau de bord |
| GET | `http://127.0.0.1:8000/admin/` | Ouvrir l’administration Django |

Le tableau de bord `/dashboard/` est encore le prototype historique et lit `/api/get` (`Dht11`). Les nouvelles mesures du capteur sont visibles dans `/admin/` sous **Monitoring → Measurements**; le tableau de bord sera raccordé au nouveau modèle lors d’une tâche frontend/API ultérieure.

Avant l’ingestion, créer dans `/admin/` un réfrigérateur, un capteur lié et une politique de seuil globale (ou spécifique). Puis générer un identifiant capteur à usage unique :

```bash
python manage.py issue_sensor_credential <sensor-uuid>
```

La commande affiche une seule fois la valeur à stocker dans le firmware et révoque les anciens identifiants du capteur. Envoyer l’en-tête `Authorization: Sensor <uuid>.<secret>` et un `external_id` stable et unique par mesure; réutiliser le même identifiant lors d’une nouvelle tentative.

Exemple moderne :

```json
{"external_id":"sensor-seq-1042","temperature":4.7,"humidity":54.0,"measured_at":"2026-11-21T12:00:00Z"}
```

Pour conserver le corps historique à `/api/post`, envoyer `{"temp":24.5,"hum":54.0}` avec le même en-tête d’authentification et `Idempotency-Key: sensor-seq-1042`. Le chemin reste compatible, mais les anciennes requêtes anonymes ne sont plus acceptées. La réponse legacy conserve les champs `temp`, `hum` et `dt`; la mesure est stockée dans `Measurement`, pas dans l’ancienne table `Dht11`. Une création renvoie `201`, un rejeu idempotent renvoie `200`.

## Vérification

```bash
python manage.py check
python manage.py showmigrations
```

La base `db-v2.sqlite3` est créée localement lors de `migrate` et n’est pas destinée à être versionnée. Les dépendances Python sont décrites dans `requirements.txt`.

## Sécurité

- Ne pas committer `.env`, la base locale ou des identifiants Wi-Fi, e-mail, Telegram et API.
- Cette fondation ne déclenche pas encore d’alertes e-mail ou Telegram.
- `runserver` est le serveur de développement Django ; ne pas l’exposer à Internet ni l’utiliser en production.
- Le dépôt contient actuellement des secrets dans un ancien commit Git. Le retrait du code ne supprime pas les valeurs de l’historique : révoquez/renouvelez immédiatement le mot de passe d’application Gmail et le jeton Telegram, puis nettoyez l’historique avant de publier ou partager le dépôt.
