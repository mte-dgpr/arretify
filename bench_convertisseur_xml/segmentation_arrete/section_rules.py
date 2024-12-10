"""Preprocess the file to detect the section levels and prepare patterns."""


import re

from .config import section_from_name
from .utils import clean_markdown


NUMBERING_PATTERN = r"(?:[IVXivx]+|\d+|[a-zA-Z])+"
OPTIONAL_SEPARATION_PATTERN = r"(?:\.?\s*(?::|–|-|–)?\s*(.+))?$"
MANDATORY_SEPARATION_PATTERN = r"\.?\s*[-]\s+(.+)$"


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

        if section_type == 'title':
            # Keep all titles
            filtered_patterns[key] = patterns[key]
            filtered_levels[key] = patterns_levels[key]
        elif section_type == 'chapter':
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


def filter_max_level_sections(sections_dict, levels_dict):

    # Group sections by their base type (without _number suffix)
    grouped_sections = {}

    for section_name in sections_dict:
        # Extract base name (e.g., 'article' from 'article_0')
        base_name = "_".join(section_name.split('_')[:-1])

        # Initialize group if not exists
        if base_name not in grouped_sections:
            grouped_sections[base_name] = []

        # Add section to its group
        grouped_sections[base_name].append({
            'full_name': section_name,
            'pattern': sections_dict[section_name],
            'level': levels_dict[section_name]
        })

    # Initialize output dictionaries
    filtered_patterns = {}
    filtered_levels = {}

    # For each group, keep only the highest level section
    for base_name, sections in grouped_sections.items():
        # Find the maximum level in this group
        max_level = max(section['level'] for section in sections)

        # Keep only sections with the maximum level
        max_level_sections = [
            section for section in sections
            if section['level'] == max_level
        ]

        # Add all max level sections to the result
        for section in max_level_sections:
            filtered_patterns[section['full_name']] = section['pattern']
            filtered_levels[section['full_name']] = section['level']

    return filtered_patterns, filtered_levels


def reorder_section_levels(patterns, patterns_levels):

    sections_order = ["title", "chapter", "article", "sub_article"]

    # Create mapping of section prefixes to their presence
    present_sections = {
        prefix: any(name.startswith(prefix) for name in patterns)
        for prefix in sections_order
    }

    # Count missing sections before each position
    missing_before = {}
    missing_count = 0
    for prefix in sections_order:
        missing_before[prefix] = missing_count
        if not present_sections[prefix]:
            missing_count += 1

    # Assign new levels
    for name in patterns:
        # Find which section type this is
        section_type = next(
            prefix for prefix in sections_order
            if name.startswith(prefix)
        )

        # Get original position and subtract missing sections before it
        original_position = sections_order.index(section_type)
        new_level = original_position - missing_before[section_type]

        # Update the patterns_levels dictionary
        patterns_levels[name] = new_level

    return patterns, patterns_levels


def clean_section_names(patterns, patterns_levels):

    # Create new dictionaries with cleaned names
    cleaned_patterns = {}
    cleaned_levels = {}

    for section_name in patterns:

        # Remove the _number suffix
        base_name = "_".join(section_name.split('_')[:-1])

        # Copy values to new dictionaries with cleaned names
        cleaned_patterns[base_name] = patterns[section_name]
        cleaned_levels[base_name] = patterns_levels[section_name]

    return cleaned_patterns, cleaned_levels


def preprocess_section_types(content):

    section_names = ["titre", "chapitre", "article"]

    # Pattern to detect all types of titles, chapters and articles
    sections_pattern = "|".join(section_names)
    pattern_with_titles = fr'^({sections_pattern})\s+({NUMBERING_PATTERN}(?:\.{NUMBERING_PATTERN})*){OPTIONAL_SEPARATION_PATTERN}'
    pattern_without_titles = fr"^({NUMBERING_PATTERN}(?:\.{NUMBERING_PATTERN})*){MANDATORY_SEPARATION_PATTERN}"

    # Dicts to store the patterns and levels
    patterns = {}
    patterns_levels = {}

    for line in content:

        line = clean_markdown(line)

        # Pattern with titles
        match = re.match(pattern_with_titles, line, re.IGNORECASE)

        if match:

            section_name, numbering, content = match.groups()
            section_name = section_name.lower()

            # Level is equal to the number of unique numbers separated by points
            numbering_split = numbering.split(".")
            numbering_all = [x for x in numbering_split if len(x) > 0]
            level = len(numbering_all) - 1  # starts at zero

            # Create the corresponding pattern
            if level == 0:
                number_part = NUMBERING_PATTERN
            else:
                number_part = NUMBERING_PATTERN + fr"\.{NUMBERING_PATTERN}" * level

            # Create key name
            section_type = section_from_name(section_name).value
            key = f"{section_type}_{level}"
            if level >= 3:  # correct case where article can have 3 or 4 digits
                key = f"sub_article_{level}"

            # Fill section patterns
            patterns[key] = fr"^{section_name}\s+({number_part}){OPTIONAL_SEPARATION_PATTERN}"
            patterns_levels[key] = level

        # Pattern without titles
        match = re.match(pattern_without_titles, line, re.IGNORECASE)

        if match:

            numbering, content = match.groups()

            # Level is equal to the number of unique numbers separated by points
            numbering_split = numbering.split(".")
            numbering_all = [x for x in numbering_split if len(x) > 0]
            level = len(numbering_all) - 1  # starts at zero

            # Find section name based on level
            if level == 0 and numbering[0].lower() in {"i", "v", "x"}:
                section_type = "title"
            elif level == 0 and numbering[0].lower() in {"a", "b", "c", "d", "e", "f", "g", "h"}:
                section_type = "chapter"
            elif level == 0 and numbering[0].lower() in {"1", "2", "3", "4", "5", "6", "7", "8", "9"}:
                section_type = "article"
            elif level >= 3:  # correct case where article can have 3 or 4 digits
                section_type = "sub_article"
            else:
                section_type = "sub_article"

            # Create the corresponding pattern
            if level == 0:
                number_part = NUMBERING_PATTERN
            else:
                number_part = NUMBERING_PATTERN + fr"\.{NUMBERING_PATTERN}" * level

            # Create key name
            key = f"{section_type}_{level}"

            # Fill section patterns
            patterns[key] = fr"^({number_part}){MANDATORY_SEPARATION_PATTERN}"
            patterns_levels[key] = level

    # print(patterns, patterns_levels)

    # Filter out sections that are not under upper section levels
    # patterns, patterns_levels = filter_hierarchical_patterns(patterns, patterns_levels)
    # print(patterns, patterns_levels)

    # Filter out only max levels per section
    patterns, patterns_levels = filter_max_level_sections(patterns, patterns_levels)
    # print(patterns, patterns_levels)

    # Rearrange section levels to match XML indentation
    patterns, patterns_levels = reorder_section_levels(patterns, patterns_levels)
    # print(patterns, patterns_levels)

    # Remove suffix levels in section names
    patterns, patterns_levels = clean_section_names(patterns, patterns_levels)
    # print(patterns, patterns_levels)

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
        "1.2 - Sous-article",
        "1.2. - Sous-article",
        "I - Titre ou chapitre",
        "Ceci n'est pas un titre",
        "A la bonne journée",
    ]

    PATTERNS, _ = preprocess_section_types(test_content)

    print("Patterns détectés:")
    for KEY, PATTERN in PATTERNS.items():
        print(f"{KEY}: {PATTERN}")
