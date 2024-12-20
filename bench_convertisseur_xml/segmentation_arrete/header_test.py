import unittest
import re

from .header import _process_entity_pile


class TestProcessEntityPile(unittest.TestCase):

    def test_simple(self):
        pile = ['Préfecture du Doubs DIRECTION DES COLLECTIVITÉS LOCALES ET DE L\'ENVIRONNEMENT BUREAU DE L\'ENVIRONNEMENT']
        assert _process_entity_pile(pile) == [
            'Préfecture du Doubs ',
            'DIRECTION DES COLLECTIVITÉS LOCALES ET DE L\'ENVIRONNEMENT ',
            'BUREAU DE L\'ENVIRONNEMENT',
        ]
