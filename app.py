import flask
import feedparser
import requests
import re
from flask_caching import Cache

app = flask.Flask(__name__)
cache = Cache(app, config={
    'CACHE_TYPE': 'memcached',
    'CACHE_DEFAULT_TIMEOUT': 60,
    'CACHE_KEY_PREFIX': 'flrig.beesbuzz.biz',
})

@cache.cached()
def get_feed(tag=None):
    params = {'format': 'atom'}
    if tag:
        params['tags'] = tag

    req = requests.get(
        'https://api.flickr.com/services/feeds/photos_public.gne', params=params)
    feed = feedparser.parse(req.text)

    return feed


def filter_description(content):
    lines = content.splitlines()[2:]

    return flask.Markup('\n'.join(lines))


@app.route('/')
@app.route('/<string:tag>')
@cache.cached()
def flrig(tag=None):
    if flask.request.args.get('tag'):
        return flask.redirect(flask.url_for('flrig', tag=flask.request.args.get('tag')), 301)

    return flask.render_template(
        'flrig.html',
        feed=get_feed(tag),
        tag=tag,
        filter_description=filter_description)


@app.route('/robots.txt')
def robots_txt():
    return flask.send_file('robots.txt')

if __name__ == '__main__':
    app.run(debug=True)

