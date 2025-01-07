import re
import unittest
from typing import Pattern, Iterator

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.types import ModificationType
from bench_convertisseur_xml.utils.generators import remove_empty_strings_from_flow
from .modification_segments import _tag_modification_segments, _preprocess_children_by_adding_target_groups, TargetGroup

class TestTagModificationSegments(unittest.TestCase):

    def test_before_and_after(self):
        # Arrange
        soup = BeautifulSoup('<div>Sentence before. bla haha bli <i>target</i> bla hoho ble. Sentence after.</div>', features='html.parser')
        targets = soup.select('i')
        patterns = [
            (re.compile(r'haha'), ModificationType.UPDATE), 
            (re.compile(r'hoho'), ModificationType.DELETE),
            # Should be ignored since others will match first
            (re.compile(r'\w{4}'), ModificationType.ADD),
        ]

        # Act
        result = list(_tag_modification_segments(soup, list(soup.div.children), targets, patterns))

        # Assert
        assert [str(element) for element in result] == [
            "Sentence before.",
            " bla ", 
            "<span class=\"dsr-modification_segment\" data-keyword=\"haha\" data-modification_type=\"update\"><b>haha</b> bli </span>",
            "<i>target</i>", 
            "<span class=\"dsr-modification_segment\" data-keyword=\"hoho\" data-modification_type=\"delete\"> bla <b>hoho</b></span>",
            " ble",
            ". Sentence after."
        ]

    def test_several(self):
        # Arrange
        soup = BeautifulSoup('<div>Sentence before. bla haha bli <i>target1</i> bla hoho ble. Hoho. Bly bly <i>target2</i> haha wow.</div>', features='html.parser')
        targets = soup.select('i')
        patterns = [
            (re.compile(r'haha'), ModificationType.UPDATE),
        ]

        # Act
        result = list(_tag_modification_segments(soup, list(soup.div.children), targets, patterns))

        # Assert
        assert [str(element) for element in result] == [
            "Sentence before.",
            " bla ", 
            "<span class=\"dsr-modification_segment\" data-keyword=\"haha\" data-modification_type=\"update\"><b>haha</b> bli </span>",
            "<i>target1</i>", 
            " bla hoho ble",
            ". Hoho.",
            " Bly bly ",
            "<i>target2</i>", 
            "<span class=\"dsr-modification_segment\" data-keyword=\"haha\" data-modification_type=\"update\"> <b>haha</b></span>",
            " wow",
            "."
        ]

    def test_no_match(self):
        # Arrange
        soup = BeautifulSoup('<div>Sentence before. bla haha bli <i>target</i> bla hoho ble. Sentence after.</div>', features='html.parser')
        targets = soup.select('i')
        patterns = [
            (re.compile(r'WHAT\?'), ModificationType.UPDATE), 
        ]

        # Act
        result = list(_tag_modification_segments(soup, list(soup.div.children), targets, patterns))

        # Assert
        assert [str(element) for element in result] == [
            "Sentence before.",
            " bla haha bli ",
            "<i>target</i>", 
            " bla hoho ble",
            ". Sentence after.",
        ]

    def test_match_before_and_after_no_remaining_text(self):
        # Arrange
        soup = BeautifulSoup('<div>haha bli <i>target</i> bla haha</div>', features='html.parser')
        targets = soup.select('i')
        patterns = [
            (re.compile(r'haha'), ModificationType.UPDATE), 
        ]

        # Act
        result = list(_tag_modification_segments(soup, list(soup.div.children), targets, patterns))

        # Assert
        assert [str(element) for element in result] == [
            "<span class=\"dsr-modification_segment\" data-keyword=\"haha\" data-modification_type=\"update\"><b>haha</b> bli </span>",
            "<i>target</i>", 
            "<span class=\"dsr-modification_segment\" data-keyword=\"haha\" data-modification_type=\"update\"> bla <b>haha</b></span>",
        ]


class TestIterTargetAndSiblingsGroups(unittest.TestCase):

    def test_with_several_groups_touching(self):
        # Arrange
        soup = BeautifulSoup('<div>bla haha bli <i>target1</i> bla hoho. ble <i>target2</i> bly blu. Poi</div>', features='html.parser')
        target_tags = soup.select('i')
        assert len(target_tags) == 2

        # Act
        result = list(_preprocess_children_by_adding_target_groups(soup, list(soup.div.children), target_tags))

        # Assert
        assert [str(element) if isinstance(element, Tag) else element for element in result] == [
            TargetGroup('bla haha bli ', target_tags[0], ' bla hoho'),
            '.',
            TargetGroup(' ble ', target_tags[1], ' bly blu'),
            '. Poi'
        ]

    def test_with_overlap(self):
        # Arrange
        soup = BeautifulSoup('<div>bla haha bli <i>target1</i> bla hoho ble <i>target2</i> bly blu</div>', features='html.parser')
        target_tags = soup.select('i')
        assert len(target_tags) == 2

        # Act
        result = list(_preprocess_children_by_adding_target_groups(soup, list(soup.div.children), target_tags))

        # Assert
        assert [str(element) if isinstance(element, Tag) else element for element in result] == [
            TargetGroup('bla haha bli ', target_tags[0], ' bla hoho ble '),
            TargetGroup(None, target_tags[1], ' bly blu'),
        ]

    def test_with_several_groups_first_and_end(self):
        # Arrange
        soup = BeautifulSoup('<div><i>target1</i> bla hoho. ble <i>target2</i></div>', features='html.parser')
        target_tags = soup.select('i')
        assert len(target_tags) == 2

        # Act
        result = list(_preprocess_children_by_adding_target_groups(soup, list(soup.div.children), target_tags))

        # Assert
        assert [str(element) if isinstance(element, Tag) else element for element in result] == [
            TargetGroup(None, target_tags[0], ' bla hoho'),
            '.',
            TargetGroup(' ble ', target_tags[1], None),
        ]

    def test_with_other_tag(self):
        # Arrange
        soup = BeautifulSoup('<div>bla haha bli <i>target1</i> bla hoho ble <b>target2</b> bly blu</div>', features='html.parser')
        target_tags = soup.select('i')
        assert len(target_tags) == 1

        # Act
        result = list(_preprocess_children_by_adding_target_groups(soup, list(soup.div.children), target_tags))

        # Assert
        assert [str(element) if isinstance(element, Tag) else element for element in result] == [
            TargetGroup('bla haha bli ', target_tags[0], ' bla hoho ble '),
            '<b>target2</b>',
            ' bly blu',
        ]