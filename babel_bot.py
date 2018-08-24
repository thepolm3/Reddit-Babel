"""Summon Babel_Bot on reddit with !babel <sometext> to have
the relevant page linked to you

author /u/thepolm3
"""


import re
import requests
import praw
from secret import client_id, client_secret, username, password

with open('subreddits.txt') as f:
    ACTIVE_SUBREDDITS = f.read().split('\n')

KEYWORD = '!babel'
DOWNVOTE_THRESHOLD = -5

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

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=password,
                     username=username,
                     user_agent=f'Python:babel_bot:v1 (by /u/thepolm3)',
                     )


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

def main():
    """main routine"""

    processed_comments = set()

    print('Performing setup tasks')
    bot = reddit.redditor(username)

    for comment in bot.comments.new(limit=None):
        if comment.parent().id not in processed_comments:
            processed_comments.add(comment.parent().id)

        if comment.score <= DOWNVOTE_THRESHOLD:
            print(f'Deleting {comment.permalink} at {comment.score} votes')
            comment.delete()

    print(f'Running {username}')
    subreddits = reddit.subreddit('+'.join(ACTIVE_SUBREDDITS))
    for comment in subreddits.stream.comments():

        #We've already done this one
        if comment.id in processed_comments:
            continue

        text = comment.body.lower()

        #too short to contain our keyword
        if len(text) <= len(KEYWORD) + 1:
            continue

        #too long to search in babel
        if len(text) > 3200 - len(KEYWORD):
            continue

        #an unrelated comment
        if not text.startswith(KEYWORD):
            continue

        mode = 0
        if text[len(KEYWORD)] in '1234':
            mode = int(text[len(KEYWORD)]) - 1

        text = ''.join([ch for ch in text[len(KEYWORD):] if ch in ALLOWED_CHARS]).strip()


        print(f'request by /u/{comment.author.name} to find "{text}"')

        urls = list(babel_search(text))
        reply_text = REPLY_TEMPLATE.format(url=urls[mode])

        print(f'Replying to /u/{comment.author.name} in {comment.permalink}')

        comment.reply(reply_text)
        processed_comments.add(comment.id)


if __name__ == '__main__':
    #print(list(babel_search('testing program')))
    main()
