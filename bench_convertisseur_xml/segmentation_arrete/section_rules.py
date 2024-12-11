"""Preprocess the file to detect the section levels and prepare patterns."""


import re
from collections import defaultdict

from .utils import clean_markdown


NUMBERING_PATTERN = r"(?:[IVXivx]+|\d+|[a-zA-Z])+"
SEPARATION_PATTERN = r"(?:\.?\s*[-–]?\s*(.+))?$"


def filter_hierarchical_patterns(patterns: dict, patterns_levels: dict):

    # Extract maximum levels for titles and chapters
    titre_levels = set(int(k.split('_')[1]) for k in patterns.keys() if k.startswith('titre_'))
    chapitre_levels = set(int(k.split('_')[1]) for k in patterns.keys() if k.startswith('chapitre_'))

    # Find maximal title level
    max_titre = max(titre_levels) if titre_levels else -1

    # Filter patterns and levels
    filtered_patterns = {}
    filtered_levels = {}

    for key in patterns:
        section_type, level = key.split('_')
        level = int(level)

        if section_type == 'titre':
            # Keep all titles
            filtered_patterns[key] = patterns[key]
            filtered_levels[key] = patterns_levels[key]
        elif section_type == 'chapitre':
            # Keep chapters with level greater than titles
            if level > max_titre:
                filtered_patterns[key] = patterns[key]
                filtered_levels[key] = patterns_levels[key]
        elif section_type == 'article':
            # Keep articles with level greater than titles and chapters
            if level > max_titre and level > max(chapitre_levels, default=-1):
                filtered_patterns[key] = patterns[key]
                filtered_levels[key] = patterns_levels[key]

    return filtered_patterns, filtered_levels


def preprocess_section_types(content):

    section_types = ["titre", "chapitre", "article"]

    # Pattern to detect all types of titles, chapters and articles
    sections_pattern = "|".join(section_types)
    base_pattern = fr'^({sections_pattern})\s+({NUMBERING_PATTERN}(?:\.{NUMBERING_PATTERN})*){SEPARATION_PATTERN}'

    # Dicts to store the patterns and levels
    patterns = {}
    patterns_levels = {}

    for line in content:

        line = clean_markdown(line)

        match = re.match(base_pattern, line, re.IGNORECASE)

        if match:

            section_type, numbering, content = match.groups()
            section_type = section_type.lower()

            # Level is equal to the number of unique numbers separated by points
            numbering_split = numbering.split(".")
            numbering_all = [x for x in numbering_split if len(x) > 0]
            level = len(numbering_all) - 1  # starts at zero

            # Create the corresponding pattern
            if level == 0:
                number_part = NUMBERING_PATTERN
            else:
                number_part = NUMBERING_PATTERN + fr"\.{NUMBERING_PATTERN}" * level

            key = f"{section_type}_{level}"
            patterns[key] = fr"^{section_type.upper()}\s+({number_part}){SEPARATION_PATTERN}"
            patterns_levels[key] = level

    # Sanity check
    patterns, patterns_levels = filter_hierarchical_patterns(patterns, patterns_levels)

    return patterns, patterns_levels




if __name__ == "__main__":

    # Test du code avec différents formats
    test_content = [
    "TITRE I - Premier titre",
    "TITRE 1 - Autre titre",
    "ARTICLE 1",
    "CHAPITRE A.1 - Premier chapitre",
    "CHAPITRE 1.1.2 - Deuxième chapitre",
    "ARTICLE 1.a.3 - Premier article",
    "ARTICLE IV.2.1 - Deuxième article",
    "ARTICLE 1.1.1.1 - Troisième article",
    ]

    patterns, patterns_levels = preprocess_section_types(test_content)

    print("Patterns détectés:")
    for key, pattern in patterns.items():
        print(f"{key}: {pattern}")
