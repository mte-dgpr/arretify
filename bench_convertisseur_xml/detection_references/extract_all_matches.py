import os
import json
import re
from pathlib import Path

PARAGRAPH_SPLIT_RE = re.compile(r'(?:\s*\n\s*){2,}')


def main(input_dir: Path, output_file: Path, search: str):
    matched_paragraphs = []
    for p in input_dir.rglob("*.txt"):
        contents = open(p, 'r', encoding='utf-8').read()
        paragraphs = PARAGRAPH_SPLIT_RE.split(contents)
        for paragraph in paragraphs:
            if re.search(search, paragraph):
                matched_paragraphs.append(paragraph)
    with open(output_file, 'w', encoding='utf-8') as fd:
        fd.write(json.dumps(matched_paragraphs, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option(
        "-i", 
        "--input_dir",
    )
    parser.add_option(
        "-o", 
        "--output_file",
    )
    parser.add_option(
        "-s", 
        "--search",
    )
    (options, args) = parser.parse_args()

    main(
        Path(options.input_dir), 
        Path(options.output_file),
        options.search,
    )