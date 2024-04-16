""" Flickr Random Image Generatr """

import feedparser
import flask
import requests
import werkzeug.exceptions as http_error
import wordfilter
from flask_caching import Cache

app = flask.Flask(__name__)
cache = Cache(app, config={
    'CACHE_TYPE': 'memcached',
    'CACHE_DEFAULT_TIMEOUT': 60,
    'CACHE_KEY_PREFIX': 'flrig.beesbuzz.biz',
})


def get_feed(tag=None):
    """ Retrieve the Flickr feed, with the optional tag """
    params = {'format': 'atom'}
    if tag:
        params['tags'] = tag

    req = requests.get(
        'https://api.flickr.com/services/feeds/photos_public.gne', params=params,
        timeout=30)
    feed = feedparser.parse(req.text)

    wfilter = wordfilter.Wordfilter()

    for item in feed['entries']:
        item_tags = []
        for itag in item['tags']:
            if 'term' in itag and not wfilter.blacklisted(itag['term']):
                item_tags.append(itag)
        item['tags'] = item_tags

    return feed


def filter_description(content):
    """ Fix the item description """
    lines = content.splitlines()[2:]

    return flask.Markup('\n'.join(lines))


@app.route('/')
@app.route('/<string:tag>')
@cache.cached()
def flrig(tag=None):
    """ main page handler """
    if tag and wordfilter.Wordfilter().blacklisted(tag):
        raise http_error.NotFound("I don't know what that word means")

    return flask.render_template(
        'flrig.html',
        feed=get_feed(tag),
        tag=tag,
        filter_description=filter_description)


@app.route('/robots.txt')
def robots_txt():
    """ robots.txt handler """
    return flask.send_file('robots.txt')


if __name__ == '__main__':
    app.run(debug=True)
