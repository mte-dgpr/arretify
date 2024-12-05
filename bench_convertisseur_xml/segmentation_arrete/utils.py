"""Utilitary funtions."""


import re


def clean_markdown(text: str) -> str:

    # Remove newline at the end
    text = re.sub(r'[\n\r]+$', '', text)

    # Remove * at the beginning only if not followed by space
    text = re.sub(r"^\*+(?!\s)", "", text)

    # Remove * at the end only if not preceded by space 
    text = re.sub(r"(?<!\s)\*+$", "", text)

    # Remove any number of # or whitespaces at the beginning of the sentence
    text = re.sub(r"^[#\s]+", "", text)

    return text
