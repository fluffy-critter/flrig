import flask
import feedparser
import requests
import re

app = flask.Flask(__name__)


def get_feed(tag=None):
    params = {'format': 'atom'}
    if tag:
        params['tag'] = tag

    req = requests.get(
        'http://api.flickr.com/services/feeds/photos_public.gne', params=params)
    feed = feedparser.parse(req.text)

    return feed


def filter_description(content):
    lines = content.splitlines()[2:]

    return flask.Markup('\n'.join(lines))


@app.route('/')
@app.route('/<string:tag>')
def flrig(tag=None):
    return flask.render_template(
        'flrig.html',
        feed=get_feed(tag),
        tag=tag,
        filter_description=filter_description)

if __name__ == '__main__':
    app.run(debug=True)
