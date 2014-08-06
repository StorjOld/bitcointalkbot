#!/usr/bin/env python3

# Written by Jonathon Vogel, 2014

import bs4
import feedparser
import requests
import slack
import slack.chat
import time
import traceback
import urllib.parse

KEYWORDS = ['Storj', 'Storj Labs', 'SJCX', 'Storjcoin X', 'Storjcoin']
PING_TIME = 2  # how many seconds to wait between checking BitcoinTalk
KEYWORD_FORMAT = '_*{}*_'  # markdown bold, {} is replaced
MESSAGE_FORMAT = """Someone mentioned your organization on BitcoinTalk!
Thread - {} / {}
{}"""

slack.api_token = '' # get one for your org. at api.slack.com
SLACK_USERNAME = 'Bitcoin-Talk-Bot'
SLACK_CHANNEL = '#general'

BITCOIN_TALK_RSS = 'https://bitcointalk.org/index.php?type=rss;action=.xml&limit=100'

def string_find_all(s, needle):
    """A generator that finds all occurences of needle in s."""
    loc = 0
    while True:
        loc = s.find(needle, loc)
        if loc == -1:
            return
        yield loc
        loc += len(needle)


def check_and_format_string(s, kwds, each_side_context=20):
    """s is the string to check, kwds is the keywords to check for, and
    each_side_context is the number of characters of context to include on each
    side of the keyword. Returns a list of formatted strings, which is empty if
    no keywords were found.
    """

    keywords = {}
    for k in kwds:
        for loc in string_find_all(s, k):
            if loc not in keywords or len(k) > len(keywords[loc]):
                keywords[loc] = k

    return [s[loc - each_side_context:loc] + KEYWORD_FORMAT.format(k) + s[loc + len(keywords[loc]):loc + len(keywords[loc]) + each_side_context]
            for loc, k in keywords.items()]


def check_post_strings(url, kwd=KEYWORDS):
    """We need to do a *little* bit of HTML scraping, as the RSS feed only
    gives us partial summaries of posts. Luckily, this isn't too difficult,
    and it's flexible enough that BitcoinTalk redesigns shouldn't break it
    too hard.
    """
    html = bs4.BeautifulSoup(requests.get(url).text)
    post_id_elem = html.find('a', href=url)
    if post_id_elem is None: # bitcoin talk returning bad HTML
        print('Bad HTML (503?), bailing...')
        print(html[:100])
        raise Exception('Bad HTML, possible 503')
    post = post_id_elem.find_next('div', {'class': 'post'})

    def walk_post_children(node):
        if isinstance(node, str):
            yield str(node)
        elif hasattr(node, 'children') and ('class' not in node or node['class'] not in ['quote', 'quoteheader']):
            # we don't want quotes to double-report things
            for c in node.children:
                for s in walk_post_children(c):
                    yield s

    lines = []
    for s in walk_post_children(post):
        lines += check_and_format_string(s, kwd)
    return lines


def get_post_id(url):
    return int(urllib.parse.urlparse(url).fragment.replace('msg', ''))


def check_btc_talk(last_post_checked):
    """Handler for RSS and posting to Slack."""
    t = requests.get(BITCOIN_TALK_RSS).text
    feed = feedparser.parse(t)
    #if feed['bozo']:
    #    print('WARNING: XML errors in feed')
    #    print(t[:100])
    for entry in reversed(feed['entries']):
        if 'id' not in entry or (last_post_checked is not None and get_post_id(entry['id']) <= get_post_id(last_post_checked)):
            continue
        print(entry['id'])
        try:
            mentions = check_post_strings(entry['id'], KEYWORDS)
            if len(mentions):
                print('Found a mention, posting to slack...')
                slack.chat.post_message(SLACK_CHANNEL, MESSAGE_FORMAT.format(entry['title'], entry['id'], '\n'.join(mentions)), username=SLACK_USERNAME)
            last_post_checked = entry['id']
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                raise e
            print('Unhandled exception, retrying feed parse at exception point')
            traceback.print_exc()
            break
        time.sleep(1)
    return last_post_checked

def main():
    """Loop and exception handling"""
    last_post_checked = feedparser.parse(BITCOIN_TALK_RSS)['entries'][0]['id'] # don't spend a bunch of time parsing old comments
    while True:
        try:
            last_post_checked = check_btc_talk(last_post_checked)
            time.sleep(1)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                print('Being killed! Exiting...')
                break
            print('Unexpected exception, trying to continue...')
            traceback.print_exc()

if __name__ == '__main__':
    main()