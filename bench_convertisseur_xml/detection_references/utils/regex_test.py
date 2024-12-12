import unittest
import re

from .regex import split_string_with_regex, split_string_from_match, MatchNamedGroup


class TestSplitStringWithRegex(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        regex = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = [
            str_or_match if isinstance(str_or_match, str) else f'MATCH:{str_or_match.group(0)}' 
            for str_or_match in split_string_with_regex(regex, string)
        ]
        
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


class TestSplitStringFromMatch(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "<div>Bla hello 17/12/24 !!!</div>"
        regex = re.compile(r'(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{2})')

        # Act
        match = regex.search(string)
        actual_results = list(split_string_from_match(match))

        # Assert
        expected_results = [
            MatchNamedGroup(name='day', text='17'), 
            '/', 
            MatchNamedGroup(name='month', text='12'), 
            '/', 
            MatchNamedGroup(name='year', text='24'),
        ]
        assert actual_results == expected_results

    def test_remove_none_groups(self):
        # Arrange
        regex = re.compile(r'(?P<bla1>Bla)(?P<bla2>Bla)?(?P<bla3>Blo)')
        match1 = regex.search("BlaBlaBlo")
        match2 = regex.search("BlaBlo")

        # Act
        actual_results1 = list(split_string_from_match(match1))
        actual_results2 = list(split_string_from_match(match2))

        # Assert
        assert actual_results1 == [
            MatchNamedGroup(name='bla1', text='Bla'), 
            MatchNamedGroup(name='bla2', text='Bla'), 
            MatchNamedGroup(name='bla3', text='Blo'),
        ]
        assert actual_results2 == [
            MatchNamedGroup(name='bla1', text='Bla'), 
            MatchNamedGroup(name='bla3', text='Blo')
        ]

    def test_ignore_nested_groups(self):
        # Arrange
        regex = re.compile(r'Hello (?P<bly>Bla(?P<blo_nested>Blo)Bla) !!!')
        match = regex.search("<span> Hello BlaBloBla !!! </span>")

        # Act
        actual_results = list(split_string_from_match(match))

        # Assert
        assert actual_results == [
            'Hello ', 
            MatchNamedGroup(name='bly', text='BlaBloBla'),
            ' !!!',
        ]
