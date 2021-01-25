# -*- encoding: utf-8
"""Utility functions."""

import re
import math

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
    total_unique_fics = 0
    fandom_freq = {}
    relationship_freq = {}
    fic_freq = {}
    tag_freq = {}
    author_freq = {}
    for work in works:
        tmp = work['chapters'].split('/')
        num_chapters = int(tmp[0])
        num_visits = int(math.ceil(work['num_visits']/num_chapters)) # num recorded visits discounted by number of chapters
        total_words += work['words'] * num_visits 
        total_fics += num_visits 
        total_unique_fics += 1
        for rel in work['relationships']:
            if rel not in relationship_freq:
                relationship_freq[rel] = 0
            relationship_freq[rel] += num_visits
        for fandom in work['fandom']:
            if fandom not in fandom_freq:
                fandom_freq[fandom] = 0
            fandom_freq[fandom] += num_visits
        for author in work['author']:
            if author not in author_freq:
                author_freq[author] = 0
            author_freq[author] += num_visits 
        for tag in work['additional_tags']:
            if tag not in tag_freq:
                tag_freq[tag] = 0
            tag_freq[tag] += num_visits 
        fic_freq[(work['title'],tuple(work['author']))] = num_visits
    # remove uninformative results
    fandom_freq.pop('No Fandom', None)
    author_freq.pop('orphan_account', None)
    # sort by frequency
    fandom_top5 = sorted(fandom_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    relationship_top5 = sorted(relationship_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    fic_top5 = sorted(fic_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    author_top5 = sorted(author_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    tag_top5 = sorted(tag_freq.items(), key=lambda item: item[1], reverse=True)[:5]
    stats = {
        'total_words': "{:,}".format(total_words),
        'total_fics': "{:,}".format(total_fics),
        'total_unique_fics': "{:,}".format(total_unique_fics),
        'total_fandoms': "{:,}".format(len(fandom_freq)),
        'total_relationships': "{:,}".format(len(relationship_freq)),
        'top_fandoms': sorted_tuples_to_dict(fandom_top5),
        'top_relationships': sorted_tuples_to_dict(relationship_top5),
        'top_fics': sorted_tuples_to_dict(fic_top5, format_fics=True), 
        'top_authors': sorted_tuples_to_dict(author_top5),
        'top_tags': sorted_tuples_to_dict(tag_top5),
    }
    return stats

def sorted_tuples_to_dict(items, format_fics=False):
    output = []
    for item in items:
        if format_fics:
            title = item[0][0]
            authors = " & ".join(item[0][1])
            name = f"{title} by {authors}"
        else:
            name = item[0]
        output.append({'name': name, 'count': item[1]})
    return output
