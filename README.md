# Arrêtify

Cette librairie permet la conversion d'arrêtés préfectoraux OCRisées depuis du Markdown vers du HTML.

## Setup

La librairie se configure avec des variables d'environnement. Vous pourrez par exemple créer un fichier `.env` avec les variables suivantes : 

```bash
# Si vous voulez utiliser la résolution de références 
# aux textes de droit français.
LEGIFRANCE_CLIENT_ID = '<LEGIFRANCE_CLIENT_ID>'
LEGIFRANCE_CLIENT_SECRET = '<LEGIFRANCE_CLIENT_SECRET>'

# Si vous voulez utiliser la résolution de références
# aux textes de droit européen.
EURLEX_WEB_SERVICE_USERNAME = '<EURLEX_WEB_SERVICE_USERNAME>'
EURLEX_WEB_SERVICE_PASSWORD = '<EURLEX_WEB_SERVICE_PASSWORD>'

# Choix de l'environnement d'execution.
# Notez qu'en developpement tous les appels à API externe sont 
# récupérés depuis le cache (voir `law_data\dev_cache.py`)
ENV = 'development'
```

## Executer le script de parsing

Pour éxecuter le parsing sur un lot de fichiers OCRisés, copier le dossier de fichiers dans un dossier facilement accessible (e.g. `./tmp/arretes_ocr`), et exécuter la commande `main.py`. Par exemple :

```bash
python -m main -i ./tmp/arretes_ocr -o ./tmp/arretes_html
```

Il est aussi possible d'éxecuter le parsing sur un fichier unique en passant en option le chemin complet d'entrée et de sortie, par exemple :

```bash
python -m main -i ./tmp/arretes_ocr/bla.txt -o ./tmp/arretes_html/bla.html
```

## Styling des pages HTML générées

Les fichiers html sont générés à partir du template `templates/arrete.html`. Ce fichier charge les feuilles de style suivantes :

```html
<link href="/dsfr/dsfr.main.css" rel="stylesheet" />
<link href="/styles.css" rel="stylesheet" />
```

Pour un rendu correct des styles, il faudra donc générer vos fichiers HTML dans un dossier où ces feuilles de style sont disponibles (vous pourrez par exemple utiliser `tmp/` pour éviter d'ajouter des fichiers par erreur au repo git).

Télécharger [une release du DSFR](https://github.com/GouvernementFR/dsfr/releases/download/v1.13.0/dsfr-v1.13.0.zip), extraire `dist/` et le copier dans votre dossier html. Renommer `dist/` en `dsfr/`.

Copier le fichier `templates/styles.css` dans votre dossier html.

Démarrer un server HTTP à la racine de ce dossier html. Vous pouvez utiliser powershell, naviguer dans votre dossier html, puis executer la commande suivante : `python -m http.server`.


## Developpement

### Setup

Créer un environnement virtuel :

```bash
py -3.13 -m venv venv
```

Installer la librairie et ses dépendances :

```bash
pip install .[dev]
```

Dépendances optionnelles : 

- `clients_api_droit` pour résoudre les références eurlex et légifrance. Pour installer la librairie une possibilité consiste à la cloner depuis gitlab puis à l'installer localement.


#### Outils de développement

La librairie utilise les outils suivants :
- `pytest` pour les tests
- `black` pour le formattage de code automatique
- `flake8` et `flake8-bugbear` pour le linting
- `autoflake` pour la suppression automatique des imports inutilisés. Utilisation : 
    ```bash
    autoflake \
        --in-place \
        --recursive \
        --remove-all-unused-imports \
        --remove-unused-variables \
        --exclude=__init__.py \
        arretify scripts
    ```
- `pre-commit` pour la gestion des git pre-commit hooks

Afin d'initialiser les pre-commit hooks dans votre repository, lancer la commande suivante :

```bash
pre-commit install
```

Ainsi avant chaque commit un run des outils de linting sera executé pour vérifier le formattage et les fautes de style.


### Debugging

Des outils de debugging sont fournis dans le module `debug.py`

On pourra par exemple vérifier l'exhaustivité du parsing en utilisant la fonction `insert_debug_keywords`, qui permet de vérifier que tous les cas liés au parsing d'un type d'éléments ont été traités.

Par exemple :

```python
# Parse toutes les références à des articles
# e.g. article 1.2.3 du code de l'environnement
new_children = parse_all_article_references(soup, list(container.children))

# Cherche toutes les chaines de caractères 'articles?' qui n'ont pas été
# traitées et insère un tag pour pouvoir les parcourir et les vérifier manuellement.
# On pourra ainsi détecter des cas non encore traités par la fonction `parse_all_article_references`
# et tenter de les intégrer.
new_children = insert_debug_keywords(soup, new_children, 'articles?')
```

### Testing

Pour éxecuter les tests :

```bash
pytest
```

#### Snapshot testing

Le fichier `arretify/main_test.py` permet de détecter les regressions en effectuant le parsing sur tous les documents de notre base de tests de documents dans `arretes_ocr/` et en comparant le résultat obtenu avec des résultats obtenus précédemment et stocké dans `arretes_html/`.

Si les tests échouent c'est que la génération d'html a changé. Il convient donc de vérifier que c'est bien une évolution voulue et non une régression. Pour ça voici une proposition de process :

1. Re-générer les fichiers html de référence en utilisant la commande `python -m arretify.main -i test_data/arretes_ocr -o test_data/arretes_html`
2. Utiliser l'outil de diff de git (ou de vscodium) pour comparer la nouvelle version avec la version de référence
3. Régler les problèmes éventuels, puis répéter étape 1.


### Téléchargement des données de bases de droit

Afin de parser et résoudre les références citées dans les AP à des textes du droit français ou européen, nous téléchargeons grâce à divers scripts des fichiers contenant des listes de références à vérifier. Les fonctionalités pour accéder à ces références se trouvent dans le dossier `arretify/law_data`, les scripts se trouvent dans le dossier `scripts`.

Pour utiliser ces scripts, il faut installer et configurer la librairie du Data Studio Risques `py-clients-api-droit`.

#### Légifrance

Télécharger la liste des codes :

```bash
python ./scripts/download_data_legifrance.py -o ./arretify/law_data/legifrance
```
