import re
import unittest

from .markdown import clean_markdown, is_table_line


class TestTableDetection(unittest.TestCase):

    TABLE_MD_1 = '''Blabla blabla blabla.

| Rubrique | Régime (*) | Libellé de la rubrique (activité) | Nature de l’installation | Volume autorisé |
|----------|------------|-----------------------------------|-------------------------|-----------------|
| 2771    | A          | bla | 70 MW |
| 4511.2  | D          | blo | 117 t |

(*) A (Autorisation) - D (Déclaration)

** Some other description

Volume autorisé : blablabla.
'''

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


class TestCleanMarkdown(unittest.TestCase):

    def test_remove_newline_at_end(self):
        # Arrange
        text = "This is a test\n\n"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "This is a test", "Should remove trailing newlines"

    def test_remove_asterisk_at_start(self):
        # Arrange
        text = "**Test without space** bla"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "Test without space bla", "Should remove leading asterisks not followed by space"

    def test_keep_asterisk_with_space_at_start(self):
        # Arrange
        text = "* Test with space* bla"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "* Test with space* bla", "Should retain leading asterisks followed by space"

    def test_remove_asterisk_at_end(self):
        # Arrange
        text = "Test without space*"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "Test without space*", "Should remove trailing asterisks not preceded by space"

    def test_remove_hashes_and_whitespace_at_start(self):
        # Arrange
        text = "   ##   Heading"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "Heading", "Should remove leading hashes and whitespace"

    def test_remove_mixed_hashes_and_spaces(self):
        # Arrange
        text = "   # # Heading"

        # Act
        result = clean_markdown(text)

        # Assert
        assert result == "Heading", "Should remove mixed hashes and whitespace at start"
