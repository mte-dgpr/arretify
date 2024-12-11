from ..settings import TEST_DATA_DIR

from .dqclassify.tokenizer import tokenize_paragraph


if __name__ == '__main__':
    contents = open(TEST_DATA_DIR / 'arretes_segmentes' / 'blo.md', 'r', encoding='utf-8').read()
    paragraphs = contents.split('\n\n')

    for paragraph in paragraphs:
        tokenized = tokenize_paragraph(paragraph)
        print(tokenized)