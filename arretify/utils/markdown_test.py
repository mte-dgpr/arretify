import unittest

from .markdown_cleaning import clean_markdown
from .markdown_parsing import is_table_line, is_table_description
from arretify.parsing_utils.source_mapping import (
    TextSegment,
)


class TestTableDetection(unittest.TestCase):

    TABLE_MD_1 = """Blabla blabla blabla.

| Rubrique | Régime (*) | Libellé de la rubrique (activité) | Nature de l'installation | Volume autorisé |
|----------|------------|-----------------------------------|-------------------------|-----------------|
| 2771    | A          | bla | 70 MW |
| 4511.2  | D          | blo | 117 t |

(*) A (Autorisation) - D (Déclaration)

** Some other description

Volume autorisé : blablabla.
"""  # noqa: E501

    def test_is_table_line(self):
        # Arrange
        lines = self.TABLE_MD_1.split("\n")

        # Assert
        for line in lines[0:2]:
            assert not is_table_line(line)
        for line in lines[2:6]:
            assert is_table_line(line)
        for line in lines[6:]:
            assert not is_table_line(line)

    def test_is_table_description(self):
        # Arrange
        lines = self.TABLE_MD_1.split("\n")
        pile = lines[2:6]

        # Assert
        for line in lines[0:7]:
            assert not is_table_description(line, pile)
        assert is_table_description(lines[7], pile)
        assert not is_table_description(lines[8], pile)
        assert is_table_description(lines[9], pile)
        assert not is_table_description(lines[10], pile)
        assert is_table_description(lines[11], pile)


class TestCleanMarkdown(unittest.TestCase):

    def test_remove_newline_at_end(self):
        # Arrange
        text = _make_text_segment("This is a test\n\n")

        # Act
        result = clean_markdown(text)

        # Assert
        assert result.contents == "This is a test", "Should remove trailing newlines"

    def test_remove_asterisk_at_start(self):
        # Arrange
        text = _make_text_segment("**Test without space** bla")

        # Act
        result = clean_markdown(text)

        # Assert
        assert (
            result.contents == "Test without space bla"
        ), "Should remove leading asterisks not followed by space"

    def test_keep_asterisk_with_space_at_start(self):
        # Arrange
        text = _make_text_segment("* Test with space* bla")

        # Act
        result = clean_markdown(text)

        # Assert
        assert (
            result.contents == "* Test with space* bla"
        ), "Should retain leading asterisks followed by space"

    def test_remove_asterisk_at_end(self):
        # Arrange
        text = _make_text_segment("Test without space*")

        # Act
        result = clean_markdown(text)

        # Assert
        assert (
            result.contents == "Test without space*"
        ), "Should keep trailing asterisks not preceded by space"

    def test_remove_hashes_and_whitespace_at_start(self):
        # Arrange
        text = _make_text_segment("   ##   Heading")

        # Act
        result = clean_markdown(text)

        # Assert
        assert result.contents == "Heading", "Should remove leading hashes and whitespace"

    def test_remove_mixed_hashes_and_spaces(self):
        # Arrange
        text = _make_text_segment("   # # Heading")

        # Act
        result = clean_markdown(text)

        # Assert
        assert result.contents == "Heading", "Should remove mixed hashes and whitespace at start"


def _make_text_segment(string: str) -> TextSegment:
    return TextSegment(contents=string, start=(0, 0), end=(0, 0))
