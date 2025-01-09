import unittest
import re
from typing import Iterator

from .regex import (
    split_string, split_string_at_end, split_string_at_beginning, merge_match_flow, 
    split_match_by_named_groups, MatchNamedGroup, without_named_groups, StrOrMatch, merge_strings,
    sub_with_match
)


class TestSplitString(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string(pattern, string))
        
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
        pattern = re.compile(r'aaa')

        # Act
        actual_results = _convert_str_or_match_flow(split_string(pattern, string))
        
        # Assert
        expected_results = [
            "Hello."
        ]
        assert actual_results == expected_results


class TestSplitStringAtEnd(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_end(pattern, string))
        
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
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_end(pattern, string))
        
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
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_end(pattern, string))
        
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
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = split_string_at_end(pattern, string)
        
        # Assert
        expected_results = None
        assert actual_results == expected_results
    


class TestSplitStringAtBeginning(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "Hello, this is a ttt. Let's match and replace words like ttt and bbb."
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_beginning(pattern, string))
        
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
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_beginning(pattern, string))
        
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
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = _convert_str_or_match_flow(split_string_at_beginning(pattern, string))
        
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
        pattern = re.compile(r'\bttt|bbb\b')

        # Act
        actual_results = split_string_at_beginning(pattern, string)
        
        # Assert
        expected_results = None
        assert actual_results == expected_results


class TestMergeMatchFlow(unittest.TestCase):

    def test_split_with_matches(self):
        # Arrange
        pattern = re.compile(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(merge_match_flow(split_string(
            pattern,
            string,
        )))

        # Assert
        assert result == ["abc", "123def", "456ghi"]

    def test_split_with_matches_after(self):
        # Arrange
        pattern = re.compile(r"\d+")
        string = "abc123def456ghi"

        # Act
        result = list(merge_match_flow(split_string(
            pattern,
            string,
        ), after_or_before=-1))

        # Assert
        assert result == ["abc123", "def456", "ghi"]

    def test_split_with_no_matches(self):
        # Arrange
        pattern = re.compile(r"\d+")
        string = "abcdef"

        # Act
        result = list(merge_match_flow(split_string(
            pattern,
            string,
        )))

        # Assert
        assert result == ['abcdef']

    def test_split_with_match_at_start(self):
        # Arrange
        pattern = re.compile(r"\d+")
        string = "123abc456"

        # Act
        result = list(merge_match_flow(split_string(
            pattern,
            string,
        )))

        # Assert
        assert result == ["123abc", "456"]

    def test_split_with_match_at_end(self):
        # Arrange
        pattern = re.compile(r"\d+")
        string = "abc123"

        # Act
        result = list(merge_match_flow(split_string(
            pattern,
            string,
        )))

        # Assert
        assert result == ["abc", "123"]


class TestMergeStrings(unittest.TestCase):

    def test_simple(self):
        # Arrange
        match_mock1 = re.match(r"dummy1", "dummy1")
        match_mock2 = re.match(r"dummy2", "dummy2")
        input_gen = iter(["abc", match_mock1, "def", "ghi", match_mock2, "jkl", "mno"])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result[0] == "abc"
        assert result[1] == match_mock1
        assert result[2] == "defghi"
        assert result[3] == match_mock2
        assert result[4] == "jklmno"

    def test_merge_strings_with_matches(self):
        # Arrange
        match_mock = re.match(r"dummy", "dummy")
        input_gen = iter(["abc", match_mock, "def"])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result[0] == "abc"
        assert result[1] == match_mock
        assert result[2] == "def"

    def test_with_empty_before_and_after(self):
        # Arrange
        match_mock = re.match(r"dummy", "dummy")
        input_gen = iter(["", match_mock, ""])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result[0] == ""
        assert result[1] == match_mock
        assert result[2] == ""

    def test_merge_strings_with_only_matches(self):
        # Arrange
        match_mock1 = re.match(r"dummy1", "dummy1")
        match_mock2 = re.match(r"dummy2", "dummy2")
        input_gen = iter([match_mock1, match_mock2])

        # Act
        result = list(merge_strings(input_gen))

        # Assert
        assert result == [match_mock1, match_mock2]


class TestSplitStringFromMatch(unittest.TestCase):
    def test_simple(self):
        # Arrange
        string = "<div>Bla hello 17/12/24 !!!</div>"
        pattern = re.compile(r'(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{2})')

        # Act
        match = pattern.search(string)
        actual_results = list(split_match_by_named_groups(match))

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
        pattern = re.compile(r'(?P<bla1>Bla)(?P<bla2>Bla)?(?P<bla3>Blo)')
        match1 = pattern.search("BlaBlaBlo")
        match2 = pattern.search("BlaBlo")

        # Act
        actual_results1 = list(split_match_by_named_groups(match1))
        actual_results2 = list(split_match_by_named_groups(match2))

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
        pattern = re.compile(r'Hello (?P<bly>Bla(?P<blo_nested>Blo)Bla) !!!')
        match = pattern.search("<span> Hello BlaBloBla !!! </span>")

        # Act
        actual_results = list(split_match_by_named_groups(match))

        # Assert
        assert actual_results == [
            'Hello ', 
            MatchNamedGroup(name='bly', text='BlaBloBla'),
            ' !!!',
        ]


class TestSubWithMatch(unittest.TestCase):

    def test_remove_full_match(self):
        # Arrange
        string = "Hello, this is a test."
        match = re.search(r"this is", string)

        # Act
        result = sub_with_match(string, match)

        # Assert
        assert result == "Hello,  a test.", "Should remove the matched substring"

    def test_remove_group_match(self):
        # Arrange
        string = "Hello, (this is) a test."
        match = re.search(r"\((.*?)\)", string)

        # Act
        result = sub_with_match(string, match, group=1)

        # Assert
        assert result == "Hello, () a test.", "Should remove the content of the matched group"

    def test_no_match(self):
        # Arrange
        string = "Hello, this is a test."
        match = re.search(r"not in string", string)

        # Act / Assert
        assert match is None, "Match should be None if pattern is not found"


class TestWithoutNamedGroups(unittest.TestCase):

    def test_simple(self):
        assert without_named_groups(r'(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)') == r'(([nN]° ?(\S+))|(\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)'


def _convert_str_or_match_flow(gen: Iterator[StrOrMatch]):
    return [
        str_or_match if isinstance(str_or_match, str) else f'MATCH:{str_or_match.group(0)}' 
        for str_or_match in gen
    ]