# -*- encoding: utf-8
"""Utility functions."""

import re

# Regex for extracting the work ID from an AO3 URL.  Designed to match URLs
# of the form
#
#     https://archiveofourown.org/works/1234567
#     http://archiveofourown.org/works/1234567
#
WORK_URL_REGEX = re.compile(
    r'^https?://archiveofourown.org/works/'
    r'(?P<work_id>[0-9]+)'
)


def work_id_from_url(url):
    """Given an AO3 URL, return the work ID."""
    match = WORK_URL_REGEX.match(url)
    if match:
        return match.group('work_id')
    else:
        raise RuntimeError('%r is not a recognised AO3 work URL')

        
def compute_work_stats(works):
    """ Given a list of works, compute statistics """
    # todo
    total_words = 0
    total_fics = 0
    fandom_freq = {}
    relationship_freq = {}
    fic_freq = {}
    tag_freq = {}
    author_freq = {}
    for work in works:
        total_words += work['words']
        total_fics += 1
        for rel in work['relationships']:
            if rel not in relationship_freq:
                relationship_freq[rel] = 0
            relationship_freq[rel] += 1
        for fandom in work['fandom']:
            if fandom not in fandom_freq:
                fandom_freq[fandom] = 0
            fandom_freq[fandom] += 1
        for author in work['author']:
            if author not in author_freq:
                author_freq[author] = 0
            author_freq[author] += 1
        for tag in work['additional_tags']:
            if tag not in tag_freq:
                tag_freq[tag] = 0
            tag_freq[tag] += 1
        fic_freq[(work['title'],tuple(work['author']))] = work['num_visits']
    fandom_top5 = sorted(fandom_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    relationship_top5 = sorted(relationship_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    fic_top5 = sorted(fic_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    author_top5 = sorted(author_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    tag_top5 = sorted(tag_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    stats = {
        'total_words': total_words,
        'total_fics': total_fics,
        'total_fandoms': len(fandom_freq),
        'total_relationships': len(relationship_freq),
        'top_fandoms': fandom_top5,
        'top_relationships': relationship_top5,
        'top_fics': fic_top5, # this is the only stat that uses num_visits, everything else uses unique fics to count
        'top_authors': author_top5,
        'top_tags': tag_top5,
    }
    return stats