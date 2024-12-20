import unittest
import re

from .regex import split_string_with_regex, split_string_from_match, MatchNamedGroup, without_named_groups


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

    def test_split_without_capture_matches(self):
        # Arrange
        regex = re.compile(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(split_string_with_regex(regex, string, capture_matches=False))

        # Assert
        assert result == ["abc", "123def", "456ghi"], "Should split string and include matches as strings"

    def test_split_with_no_matches(self):
        # Arrange
        regex = re.compile(r"\d+")
        string = "abcdef"

        # Act
        result = list(split_string_with_regex(regex, string, capture_matches=False))

        # Assert
        assert result == ["abcdef"], "Should return the original string when no matches are found"

    def test_split_with_match_at_start(self):
        # Arrange
        regex = re.compile(r"\d+")
        string = "123abc456"

        # Act
        result = list(split_string_with_regex(regex, string, capture_matches=False))

        # Assert
        assert result == ["123abc", "456"], "Should handle matches at the start of the string"

    def test_split_with_match_at_end(self):
        # Arrange
        regex = re.compile(r"\d+")
        string = "abc123"

        # Act
        result = list(split_string_with_regex(regex, string, capture_matches=False))

        # Assert
        assert result == ["abc", "123"], "Should handle matches at the end of the string"


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


class TestWithoutNamedGroups(unittest.TestCase):

    def test_simple(self):
        assert without_named_groups(r'(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)') == r'(([nN]° ?(\S+))|(\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)'
