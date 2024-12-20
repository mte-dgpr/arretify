Convertisseur arrêté prefectoral -> HTML
============================================


Setup
------

Installer les dépendences :

```
pip install -r requirements.txt
```


Executer le script de parsing
-----------------------------------

Pour éxecuter le parsing sur un lot de fichiers OCRisés, copier le dossier de fichiers dans dossier facilement accessible (e.g. `./tmp/arretes_ocr`), et exécuter la commande `main.py`. Par exemple :

```
python -m main -i ./tmp/arretes_ocr -o ./tmp/arretes_html
```

Il est aussi possible d'éxecuter le parsing sur un fichier unique en passant en option le chemin complet d'entrée et de sortie, par exemple :

```
python -m main -i ./tmp/arretes_ocr/bla.txt -o ./tmp/arretes_html/bla.html
```


Testing
-----------

Pour éxecuter les tests :

```
pytest
```

### Snapshot testing

Le fichier `bench_convertisseur_xml/main_test.py` permet de détecter les regressions en effectuant le parsing sur tous les documents de notre base de tests de documents dans `arretes_ocr/` et en comparant le résultat obtenu avec des résultats obtenus précédemment et stocké dans `arretes_html/`.

Si les tests échouent c'est que la génération d'html a changé. Il convient donc de vérifier que c'est bien une évolution voulue et non une régression. Pour ça voici une proposition de process : 

1. Re-générer les fichiers html de référence en utilisant la commande `python -m bench_convertisseur_xml.segmentation_arrete.main_test`
2. Utiliser l'outil de diff de git (ou de vscodium) pour comparer la nouvelle version avec la version de référence
3. Régler les problèmes éventuels, puis répéter étape 1. 


TODO 
-----------

- Dans les fichiers OCRisés, des commentaires `OCR-BUG-IGNORE` ont été placés. Ces derniers permettent de réparer le fichier OCRisé à la main en instruisant notre parser d'ignorer un bloc de texte qui doit être réparé au niveau de l'OCRisation et non du parsing.