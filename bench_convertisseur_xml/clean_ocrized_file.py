from bench_convertisseur_xml.utils.markdown import clean_markdown
from bench_convertisseur_xml.regex_utils import PatternProxy, join_with_or, Settings
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegments, combine_text_segments


CONTINUING_SENTENCE_PATTERN = PatternProxy(r"^[a-z]", settings=Settings(ignore_case=False))

IS_NOT_INFORMATION_PATTERN = PatternProxy(
    join_with_or([
        # Empty sentence or full of whitespaces
        r'^\s*$',

        # Bottom-page with format "X/YY"
        r'^\d+/\d+\s*$',
        # Bottom-page with format "Page X/YY"
        r'^page\s+\d+/\d+\s*$',
        # Bottom-page with format "Page X sur YY"
        r'^page\s+\d+\s+sur\s+\d+\s*$',
        # Bottom-page with format "Page X"
        r'^page\s+\d+$',

        # Sentence starting with "le demandeur/pétitionnaire entendu"
        r'^le (demandeur|pétitionnaire) entendu',
        # Sentence starting with "après communication"
        r'^apres communication\b',
        # Sentence starting with "sur proposition"
        r'^sur proposition\b',

        # French Republic
        r"république fran[cç]aise",
        # French national motto
        r"(liberté|égalité|fraternité)",
        # Phone numbers
        r'\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}',
        # Email address
        r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    ])
)


def clean_ocrized_file(lines: TextSegments) -> TextSegments:
    lines = [clean_markdown(line) for line in lines]
    lines = [line for line in lines if not _is_not_information(line.contents)]

    stitched_lines: TextSegments = []
    for line in lines:
        if _is_continuing_sentence(line.contents) and stitched_lines:
            # TODO-PROCESS-TAG
            stitched_lines[-1] = combine_text_segments(
                stitched_lines[-1].contents + ' ' + line.contents,
                [stitched_lines[-1], line],
            )
        else:
            stitched_lines.append(line)

    return stitched_lines


def _is_continuing_sentence(line: str) -> bool:
    """Detect sentence starting with lowercase character."""
    return bool(CONTINUING_SENTENCE_PATTERN.match(line))


def _is_not_information(line: str) -> bool:
    return bool(IS_NOT_INFORMATION_PATTERN.search(line))
