"""Summon Babel_Bot on reddit with /u/babel_bot <sometext> to have
the relevant page linked to you

author /u/thepolm3
"""
#TODO replace non alhabet characters with alphabet qeuivalents, e.g / -> .slash.

import re
import requests
import praw
import time
from secret import client_id, client_secret, username, password

DOWNVOTE_THRESHOLD = -5
MENTION_NAME = f'/u/{username}'.lower()

REPLY_TEMPLATE = "[Here you go]({url})    \n[I'm a bot, beep boop](/r/babel_bot)"

FULL_MATCH, RANDOM_CHARACTERS, RANDOM_ENGLISH_WORDS, TITLE = range(4)

ALLOWED_CHARS = set('abcdefghijklmnopqrstuvwxyz., ')
SEARCH_URL = 'https://libraryofbabel.info/search.cgi'
BOOK_URL = 'https://libraryofbabel.info/book.cgi?\
hex={hexid}&wall={wall}&shelf={shelf}&volume={volume}&page={page}&index={index}&offset={offset}'



HTML_REGEX = re.compile("postform\\(" + \
    "'([a-z0-9]+)','([0-9]+)','([0-9]+)'," + \
    "'([0-9]+)','([0-9]+)'(,'([0-9]+)','([0-9]+)')?\\)")
VALID_MATCHES = (0, 3, 4, 6)

def babel_search(text):
    """searches the library of babel for a string and returns the URL of the page it's on"""

    r = requests.post(SEARCH_URL, {'find':text})
    matches = HTML_REGEX.findall(r.text)

    #the regex will match more than once for each link
    for i in VALID_MATCHES:
        match = matches[i]

        keys = ('hexid', 'wall', 'shelf', 'volume', 'page', '_', 'index', 'offset')
        data = {keys[ind]:value for ind, value in enumerate(match)}

        #link will fail with leading zeros on these arguments
        for j in keys[1:4]:
            data[j] = int(data[j])

        yield BOOK_URL.format(**data)

def get_valid_string(string, valid_chars):
    """gets a string only containing valid_chars"""

    return ''.join([ch for ch in string if ch in valid_chars])

def main(reddit):
    """main routine"""

    for comment in reddit.user.me().comments.new(limit=None):

        if comment.score <= DOWNVOTE_THRESHOLD:
            print(f'Deleting {comment.permalink} at {comment.score} votes')
            comment.delete()

    for mention in reddit.inbox.mentions(limit=None):

        #we've already done this one
        if not mention.new:
            continue

        text = mention.body.lower()
        mention_index = text.lower().find(MENTION_NAME) + len(MENTION_NAME)

        if mention_index == -1:
            print(f'ERROR: not mentionend in mention {mention.id}, skipping')
            mention.mark_read()
            continue

        text = get_valid_string(text[mention_index:], ALLOWED_CHARS).strip()

        #text didn't contain legal characters (can happen e.g with numbers or just spaces)
        if len(text) == 0:
            continue

        #too long to search in babel
        if len(text) > 3200:
            continue

        print(f'request by /u/{mention.author.name} to find "{text}"')

        print('Getting link from library of babel...')

        url = list(babel_search(text))[FULL_MATCH]
        reply_text = REPLY_TEMPLATE.format(url=url)

        print(f'Replying to /u/{mention.author.name} in {reddit.comment(mention.id).permalink}')

        try:
            mention.reply(reply_text)

        except Exception as e:
            print(f'Error on comment {comment.permalink}:\n{e}\n ignoring')
       
        mention.mark_read()


if __name__ == '__main__':
    print('Getting reddit instance')

    reddit = praw.Reddit(client_id=client_id,
                 client_secret=client_secret,
                 password=password,
                 username=username,
                 user_agent='Python:babel_bot:v1 (by /u/thepolm3)',
                 )

    print(f'Running babel_bot on /u/{username}')
    while True:
        main(reddit)
        time.sleep(5)

    #print(list(babel_search('testing program')))
