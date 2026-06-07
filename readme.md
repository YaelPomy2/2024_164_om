# Module 164 — Interface de gestion de stock

Application web Flask pour gérer le stock d'un shop : sessions utilisateurs, produits, tailles et historique des connexions.

Documentation du module : https://info164.github.io/doc164ver1/index.html

## Prérequis

- **Python 3.10+** (vérifier avec `python --version`)
- **Un serveur MySQL local**, par exemple :
  - [XAMPP](https://www.apachefriends.org/) (Apache + MySQL + phpMyAdmin)
  - WAMP, MAMP, ou MySQL installé seul
- Le service **MySQL** doit être **démarré** avant de lancer l'application

## 1. Récupérer le projet

Ouvrir un terminal dans le dossier racine du projet (celui qui contient `run_mon_app.py`, `requirements.txt` et le dossier `APP_FILMS_164/`).

## 2. Configurer le fichier `.env`

À la racine du projet, le fichier `.env` contient les paramètres de connexion. Adapter les valeurs à votre machine :

```env
# MySQL
HOST_MYSQL="localhost"
USER_MYSQL="root"
PASS_MYSQL=""
PORT_MYSQL=3306
NAME_BD_MYSQL="FAVRE_YAEL_DEVA1A_STOCK_164_2026"
NAME_FILE_DUMP_SQL_BD="APP_FILMS_164/database/FAVRE_YAEL_DEVA1A_STOCK_164_2026.SQL"

# Flask
ADRESSE_SRV_FLASK="127.0.0.1"
DEBUG_FLASK=true
PORT_FLASK=5001
SECRET_KEY_FLASK="votre_cle_secrete"
STOCK_ADMIN_PASSWORD="stock"
```

- Sous **XAMPP**, l'utilisateur est souvent `root` avec un mot de passe **vide** (`PASS_MYSQL=""`).
- `NAME_BD_MYSQL` : nom de la base qui sera créée ou utilisée.
- `NAME_FILE_DUMP_SQL_BD` : chemin vers le fichier SQL du dump (depuis la racine du projet).


## 3. Importer la base de données

Le dump SQL se trouve ici :

`APP_FILMS_164/database/FAVRE_YAEL_DEVA1A_STOCK_164_2026.SQL`

### Méthode A — Script Python (recommandé)

Une fois le `.env` configuré et MySQL démarré :

```powershell
python APP_FILMS_164/database/1_ImportationDumpSql.py
```

Le script crée la base et importe les tables automatiquement.

### Méthode B — phpMyAdmin (XAMPP)

1. Démarrer **Apache** et **MySQL** dans le panneau XAMPP.
2. Ouvrir http://localhost/phpmyadmin
3. Créer une base nommée comme `NAME_BD_MYSQL` dans le `.env`.
4. Onglet **Importer** → choisir `FAVRE_YAEL_DEVA1A_STOCK_164_2026.SQL` → **Exécuter**.


## 4. Installer les dépendances Python

Toujours depuis la racine du projet :

```powershell
python -m pip install -r requirements.txt
```

Paquets installés : Flask, PyMySQL, environs, flask-wtf, wtforms, flask-cors, sqlparse.



## 5. Tester la connexion à MySQL (optionnel)

```powershell
python APP_FILMS_164/database/2_test_connection_bd.py
```

Si la connexion fonctionne, des lignes de la table `t_produit` s'affichent dans le terminal. Sinon, vérifier le `.env` et que MySQL tourne.



## 6. Lancer l'application

```powershell
python run_mon_app.py
```

Ouvrir le navigateur à l'adresse indiquée dans le terminal, en général :

**http://127.0.0.1:5001**



## 7. Première utilisation

1. Aller dans **Stock du shop** (page d'accueil) ou **Menu → Sessions**.
2. Si aucune session n'existe, **créer une première session** (nom, prénom, mot de passe).
3. Se **connecter** avec le mot de passe de la session.
4. Les connexions sont enregistrées dans **Historique de connexion** (`t_connexion`).

La session navigateur expire à la **fermeture du navigateur**.


## Structure 

APP_FILMS_164/
├── run_mon_app.py          # Point d'entrée
├── requirements.txt        # Dépendances Python
├── .env                    # Configuration (ne pas partager en production)
└── APP_FILMS_164/
    ├── database/           # Dump SQL et scripts d'import
    ├── stock_admin/        # Gestion stock et connexions
    └── templates/          # Pages HTML
