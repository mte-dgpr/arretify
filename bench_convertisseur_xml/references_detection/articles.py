import re
from typing import List, Pattern, Tuple
from dataclasses import dataclass

from bench_convertisseur_xml.utils.text import normalize_text


# articles 6.18.1 à 6.18.7 de l'annexe 2 à l'arrêté préfectoral 98/C/014 du 22 janvier 1998
# 2ème alinéa de l'article 4.1.b de l'arrêté 90/IC/035
# l'article 4.1.f de l'arrêté 90/IC/035
# l'arrêté préfectoral 90/IC/035 du 22 février 1990

# premier alinéa de l'article 4.1. c de l'arrêté 90/IC/035
# 4ème alinéa de l'article 4.1 c de l'arrêté 90/IC/035
# l'article 4.1.c de l'arrêté 90/IC/035

# articles 3 à 11 de l'arrêté ministériel du 10 mai 1993 relatif aux stockages de gaz inflammables liquéfiés

# l'article 8 de ce même arrêté ministériel

# l'article 11 de l'arrêté ministériel

# loi du 19 juillet 1976

# arrete ministeriel du 2 fevrier 1998


@dataclass
class ArticleReference:
    number: List[int]


ARTICLE_RE = re.compile(r'article (?P<number>(\d+\.)*(\d)+)')


def _parse_articles(article_re_list: List[Pattern], text: str) -> Tuple[List[ArticleReference], str | None]:
    articles_refs: List[ArticleReference] = []
    articles_failed: List[str] = []
    remainder = text
    for article_re in article_re_list:
        matches, remainder = normalize_text(article_re, remainder, '<ArticleRef>')
        for match in matches:
            match_dict = match.groupdict()
            number = [int(n) for n in match_dict.get('number').split('.')]
            reference = ArticleReference(
                number=number,
            )
            articles_refs.append(reference)

    if 'article' in remainder:
        return articles_refs, remainder
    else:
        return articles_refs, None
