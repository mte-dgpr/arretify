# Arrêtify

<img src="images/cover.svg" style="display:block;margin:auto;width:100%" />

<br/>

**Arrêtify** est une librairie Python permettant la conversion d’arrêtés préfectoraux français en **HTML sémantique**. [Le document résultant est structuré](./arretify/semantic_tag_specs.py) au moyen de **data attributes** (ex. `data-spec="header"`, `data-spec="section"`, etc.) et enrichi de nombreuses métadonnées (dates, références juridiques, titres d’articles, etc.). 

*⚠️ Statut : **ALPHA**, développement actif. N’hésitez pas à l’essayer, à nous faire vos retours et à contribuer ! À ce stade, nous déconseillons un usage en production.*

---

### → Pourquoi du HTML Sémantique ?

* **Data & IA-ready** : accès précis et facile aux données, ouvrant la voie à des cas d'usages variés - indexation, RAG, entrainement, etc.
* **Web-ready** : affichage direct dans un navigateur, intégration simple à toute stack web ou CMS.
* **Léger et portable** : un simple fichier HTML encapsule tout le contenu enrichi, sans dépendance serveur.


### → Fonctionnalités clés

* **Formats d'entrée** : PDF, Markdown
* **Intégration OCR** : compatible « out-of-the-box » avec Mistral OCR.
* **Entièrement modulaire** : collection de steps de traitement qui peuvent être chaînés pour construire un pipeline adapté aux besoins de l'utilisateur.
* **Enrichissement sémantique** : steps optionnels permettant d'enrichir le HTML en métadonnées : 
    - *détection de références* - droit français, droit européen, arrêtés connexes
    - *opérations de modification* - abrogation, modification, d'arrêtés connexes

### → [Exemples en ligne](https://mte-dgpr.github.io/arretify/examples/)


## Démarrage rapide

**→ Installation** : 

```bash
# Installe la dernière version d'arrêtify
pip install arretify

# Modèles spacy
python -m spacy download fr_dep_news_trf
```

Plus d'options d'installation, voir la section [options d'installation](#options_d_installation)


**→ Utilisation avec le CLI** : 

```bash
arretify -i /path/to/ocr.md -o /path/to/output.html
```

Pour directement convertir un document pdf, il vous faudra configurer votre clé mistral. [Voir la partie configuration](#configuration).


**→ Utilisation depuis Python** : 

Convertir un document markdown (résultat d'une opération d'OCR) en HTML: 

```python
from pathlib import Path
from arretify.pipeline import save_html_file, run_pipeline, load_ocr_file
from arretify.types import SessionContext
from arretify.settings import Settings

save_html_file(
    Path('/path/to/output.html'),
    run_pipeline(
        load_ocr_file(
            SessionContext(settings=Settings()),
            Path('/path/to/ocr.md'),
        )
    ),
)
```

<a id="configuration"></a>
## Configuration

La librairie se configure avec des variables d'environnement. Vous pourrez par exemple créer un fichier `.env` avec les variables suivantes : 

```bash
# Si vous voulez utiliser Mistral OCR
MISTRAL_API_KEY ='<MISTRAL_API_KEY>'

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


## CLI

Pour éxecuter le parsing sur un lot de fichiers OCRisés, copier le dossier de fichiers dans un dossier facilement accessible (e.g. `./tmp/arretes_ocr`), et exécuter la commande `main.py`. Par exemple :

```bash
python -m main -i ./tmp/arretes_ocr -o ./tmp/arretes_html
```

Il est aussi possible d'éxecuter le parsing sur un fichier unique en passant en option le chemin complet d'entrée et de sortie, par exemple :

```bash
python -m main -i ./tmp/arretes_ocr/bla.txt -o ./tmp/arretes_html/bla.html
```

<a id="options_d_installation"></a>

## Options d'installation

Arretify est plus rapide et performant avec un GPU.
Vous pouvez alors installer les dépendances optionnelles suivantes : 

```bash
# Adapter selon votre version de cuda
# Pour torch : https://pytorch.org/get-started/locally/
# Pour spacy : https://spacy.io/usage
pip install torch~=2.8.0 --extra-index-url https://download.pytorch.org/whl/cu128
pip install spacy[cuda12x]~=3.8.7
```


## Developpement

### Setup

Installer la librairie et ses dépendances en mode développement :

```bash
pip install -e .[dev]  # Sur Linux
pip install -e .[dev] --extra-index-url https://download.pytorch.org/whl/cu128  # Sur Windows, version CUDA à adapter selon votre cas

# Modèles spacy
python -m spacy download fr_dep_news_trf
```

Initialiser les sous-modules Git (qui se trouvent dans `arretify/_vendor`) : 

```bash
git submodule update --init --recursive
```

#### Outils de développement

La librairie utilise les outils suivants :
- `pytest` pour les tests
- `mypy` for static type-checking
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
- `licenseheaders` pour la gestion des en-têtes de licence dans les fichiers de code source.
- `pre-commit` pour la gestion des git pre-commit hooks

Afin d'initialiser les pre-commit hooks dans votre repository, lancer la commande suivante :

```bash
pre-commit install
```

Ainsi avant chaque commit un run des outils de linting sera executé pour vérifier le formattage et les fautes de style.


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

### Publication sur PyPI

La publication sur PyPI se fait automatiquement à travers GitHub Actions. Cette action est définie dans le workflow [.github/workflows/publish.yml](.github/workflows/publish.yml).

Pour publier une nouvelle version : 

1. Créer une branche de release `git checkout -b v1.2.3`
2. Incrémenter le numéro de version dans `pyproject.toml`
3. Ajouter un log dans le fichier `CHANGELOG.md`
4. Réinstaller la librairie si besoin, puis regénérer les HTML des exemples pour mettre à jour le numéro de version
5. Effectuer un commit et pusher la branche
6. Ajouter un tag de version correspondant au nouveau numéro de version de la librairie : 

```bash
git tag v1.2.3          # Crée le tag localement
git push origin v1.2.3  # Push sur github
```

7. Terminer par une PR