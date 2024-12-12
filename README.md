Convertisseur arrêté prefectoral -> XML
============================================

Tester localement
------------------------------

Installer les dépendences :

```
pip install -r requirements.txt
```

Lancer un script :

```
python -m bench_convertisseur_xml.segmentation_arrete.main
```

TO-DO:
- répétition des titres/chapitres/articles en début de page
- répétition du nom de la société en début de page
- nom de l'entité sur plusieurs lignes en début d'arrêté 
- texte du titre/chapitre sur la ligne suivante (sans point, regarder ça ?)
