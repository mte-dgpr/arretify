import unittest

from .sentence_rules import (
    is_table_description,
    is_line_with_semicolumn,
)


class TestTableDetection(unittest.TestCase):

    TABLE_MD_1 = """Blabla blabla blabla.

| Rubrique | Régime (*) | Libellé de la rubrique (activité) | Nature de l’installation | Volume autorisé |
|----------|------------|-----------------------------------|-------------------------|-----------------|
| 2771    | A          | bla | 70 MW |
| 4511.2  | D          | blo | 117 t |

(*) A (Autorisation) - D (Déclaration)

** Some other description

Volume autorisé : blablabla.
"""  # noqa: E501

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


class TestIsLinedContinued(unittest.TestCase):

    def test_valid_lines_with_continuation(self):
        assert is_line_with_semicolumn("This is a line: ") is True
        assert is_line_with_semicolumn("This is a line:") is True
        assert is_line_with_semicolumn("This is a line :") is True
        assert is_line_with_semicolumn("This is a line : ") is True

    def test_line_without_continuation(self):
        assert is_line_with_semicolumn("This is a complete sentence.") is False
        assert is_line_with_semicolumn("This is a line with: colon in the middle.") is False
        assert is_line_with_semicolumn("") is False
        assert is_line_with_semicolumn(": ") is False
