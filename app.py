""" Flickr Random Image Generatr """

from werkzeug.middleware.proxy_fix import ProxyFix
import feedparser
import flask
import requests
import requests.exceptions
import werkzeug.exceptions as http_error
import wordfilter
from flask_caching import Cache
import logging
import logging.handlers
import os
import markupsafe
import user_agents
import uuid

APP_PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO,
                    handlers=[
                        logging.handlers.TimedRotatingFileHandler(
                            os.path.join(APP_PATH, 'logs', 'flrig.log'), when='D'),
                        logging.StreamHandler()
                    ],
                    format="%(levelname)s:%(threadName)s:%(name)s:%(message)s")

LOGGER = logging.getLogger(__name__)

app = flask.Flask(__name__)
app.secret_key = str(uuid.uuid4())

cache = Cache(app, config={
    'CACHE_TYPE': 'memcached',
    'CACHE_DEFAULT_TIMEOUT': 60,
    'CACHE_KEY_PREFIX': 'flrig.beesbuzz.biz',
})


@cache.cached()
def get_feed(tag=None):
    """ Retrieve the Flickr feed, with the optional tag """
    LOGGER.debug("getting feed for %s", tag)

    params = {'format': 'atom'}
    if tag:
        params['tags'] = tag

    req = requests.get(
        'https://api.flickr.com/services/feeds/photos_public.gne', params=params,
        timeout=10)
    feed = feedparser.parse(req.text)

    wfilter = wordfilter.Wordfilter()

    for item in feed['entries']:
        item_tags = []
        for itag in item['tags']:
            if 'term' in itag and not wfilter.blacklisted(itag['term']):
                item_tags.append(itag)
        item['tags'] = item_tags

    LOGGER.debug("finished retrieving")

    return feed


def filter_description(content):
    """ Fix the item description """
    lines = content.splitlines()[2:]

    return markupsafe.Markup('\n'.join(lines))


@app.route('/')
@app.route('/<string:tag>')
def flrig(tag=None):
    """ main page handler """
    LOGGER.debug("root %s", tag)
    if tag and wordfilter.Wordfilter().blacklisted(tag):
        raise http_error.NotFound("I don't know what that word means")

    is_bot = user_agents.parse(flask.request.headers.get('User-Agent')).is_bot

    # if there's a tag and no valid session ID, send over to the pseudo-captcha
    if tag and not is_bot and not flask.session.get('sid'):
        return flask.render_template('gatekeep.html', sid=str(uuid.uuid4())), 401

    try:
        return flask.render_template(
            'flrig.html',
            feed=get_feed(tag),
            tag=tag,
            filter_description=filter_description,
            is_bot=is_bot)
    except requests.exceptions.RequestException as ex:
        LOGGER.warning("Upstream error for tag %s", tag)
        return flask.render_template(
            'error.html',
            error=ex)


@app.route('/', methods=["POST"])
@app.route('/<string:tag>', methods=["POST"])
def gatekeep(tag=None):
    """ handle potential AI bots """
    if not flask.request.form.get('sid'):
        raise http_error.BadRequest("missing SID")

    flask.session['sid'] = flask.request.form['sid']
    return flask.redirect(flask.url_for('flrig', tag=tag))


@app.route('/robots.txt')
def robots_txt():
    """ robots.txt handler """
    return flask.send_file('robots.txt')


app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

if __name__ == '__main__':
    app.run(debug=True)
