from collections import Counter
import re


def analyze_words(text: str, top_n: int = 30):

    if not text:
        return []

    cleaned = re.sub(r"[^A-Za-z\s]", " ", text)
    words = cleaned.lower().split()

    counter = Counter(words)
    return counter.most_common(top_n)


def find_repeated_words_in_titles(titles_en, min_count: int = 3):
    
    all_words = []

    for title in titles_en:
        if not title:
            continue
        cleaned = re.sub(r"[^A-Za-z\s]", " ", title)
        words = cleaned.lower().split()
        all_words.extend(words)

    counter = Counter(all_words)
    return {word: count for word, count in counter.items() if count >= min_count}


def title_word_counts(titles_en):

    all_words = []

    for title in titles_en:
        if not title:
            continue
        cleaned = re.sub(r"[^A-Za-z\s]", " ", title)
        words = cleaned.lower().split()
        all_words.extend(words)

    return Counter(all_words)
