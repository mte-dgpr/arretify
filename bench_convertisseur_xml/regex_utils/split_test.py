import unittest
import re
from typing import Iterator

from .split import (
    split_string_with_regex, split_string_at_end_with_regex, split_string_at_beginning_with_regex, 
    split_match_by_named_groups,
)
from .types import MatchNamedGroup
from .core import MatchFlow, PatternProxy
from bench_convertisseur_xml.types import PageElementOrString


class TestSplitStringWithRegex(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            "Hello, this is a ", 
            "MATCH:ttt",
            ". Let's match and replace words like ", 
            "MATCH:ttt", 
            " and ",
            "MATCH:bbb",
            "."
        ]
        assert actual_results == expected_results

    def test_no_match(self):
        # Arrange
        string = "Hello."
        pattern = PatternProxy(r'aaa')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            "Hello."
        ]
        assert actual_results == expected_results


class TestSplitStringWithRegexAtEnd(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_end_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            "Hello, this is a ttt. Let's match and replace words like ttt and ",
            "MATCH:bbb",
            "."
        ]
        assert actual_results == expected_results

    def test_last_is_match(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb"
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_end_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            "Hello, this is a ttt. Let's match and replace words like ttt and ",
            "MATCH:bbb",
            '',
        ]
        assert actual_results == expected_results

    def test_whole_is_match(self):
        # Arrange
        string = "bbb"
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_end_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            '',
            "MATCH:bbb",
            '',
        ]
        assert actual_results == expected_results

    def test_no_match(self):
        # Arrange
        string = "aaa"
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = split_string_at_end_with_regex(pattern, string)
        
        # Assert
        expected_results = None
        assert actual_results == expected_results
    

class TestSplitStringWithRegexAtBeginning(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_beginning_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            "Hello, this is a ",
            "MATCH:ttt",
            ". Let's match and replace words like ttt and bbb.",
        ]
        assert actual_results == expected_results

    def test_first_is_match(self):
        # Arrange
        string = "ttt. Let's match and replace words like ttt and bbb."
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_beginning_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            '',
            "MATCH:ttt",
            ". Let's match and replace words like ttt and bbb.",
        ]
        assert actual_results == expected_results

    def test_whole_is_match(self):
        # Arrange
        string = "bbb"
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_beginning_with_regex(pattern, string))
        
        # Assert
        expected_results = [
            '',
            "MATCH:bbb",
            '',
        ]
        assert actual_results == expected_results

    def test_no_match(self):
        # Arrange
        string = "aaa"
        pattern = PatternProxy(r'\bttt|bbb\b')

        # Act
        actual_results = split_string_at_beginning_with_regex(pattern, string)
        
        # Assert
        expected_results = None
        assert actual_results == expected_results


class TestSplitStringFromMatch(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "<div>Bla hello 17/12/24 !!!</div>"
        pattern = PatternProxy(r'(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{2})')

        # Act
        match = pattern.search(string)
        actual_results = list(split_match_by_named_groups(match))

        # Assert
        expected_results = [
            MatchNamedGroup(group_name='day', text='17'), 
            '/', 
            MatchNamedGroup(group_name='month', text='12'), 
            '/', 
            MatchNamedGroup(group_name='year', text='24'),
        ]
        assert actual_results == expected_results

    def test_remove_none_groups(self):
        # Arrange
        pattern = PatternProxy(r'(?P<bla1>Bla)(?P<bla2>Bla)?(?P<bla3>Blo)')
        match1 = pattern.search("BlaBlaBlo")
        match2 = pattern.search("BlaBlo")

        # Act
        actual_results1 = list(split_match_by_named_groups(match1))
        actual_results2 = list(split_match_by_named_groups(match2))

        # Assert
        assert actual_results1 == [
            MatchNamedGroup(group_name='bla1', text='Bla'), 
            MatchNamedGroup(group_name='bla2', text='Bla'), 
            MatchNamedGroup(group_name='bla3', text='Blo'),
        ]
        assert actual_results2 == [
            MatchNamedGroup(group_name='bla1', text='Bla'), 
            MatchNamedGroup(group_name='bla3', text='Blo')
        ]

    def test_ignore_nested_groups(self):
        # Arrange
        pattern = PatternProxy(r'Hello (?P<bly>Bla(?P<blo_nested>Blo)Bla) !!!')
        match = pattern.search("<span> Hello BlaBloBla !!! </span>")

        # Act
        actual_results = list(split_match_by_named_groups(match))

        # Assert
        assert actual_results == [
            'Hello ', 
            MatchNamedGroup(group_name='bly', text='BlaBloBla'),
            ' !!!',
        ]


def _convert_str_or_match_flow(gen: MatchFlow):
    return [
        str_or_match if isinstance(str_or_match, str) else f'MATCH:{str_or_match.group(0)}' 
        for str_or_match in gen
    ]