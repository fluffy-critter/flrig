""" Flickr Random Image Generatr """

import logging
import logging.handlers
import os
import re
import uuid

import arrow
import feedparser
import flask
import markupsafe
import requests
import requests.exceptions
import user_agents
import werkzeug.exceptions
import wordfilter
from flask_caching import Cache
from werkzeug.middleware.proxy_fix import ProxyFix

APP_PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.WARNING,
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
    'CACHE_TYPE': 'MemcachedCache',
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


def keymaster(sid):
    """ Generates a salted token for the browser """
    import hashlib

    parts = [
        str(sid),
        flask.request.remote_addr,
        flask.request.headers.get('User-Agent')
    ]
    token = hashlib.md5('|'.join(parts).encode('utf-8')) # ty:ignore[no-matching-overload]

    return token.digest()

@app.before_request
def is_bot():
    """ simple bot detection """
    ua_string = flask.request.headers.get('User-Agent')
    flask.g.is_bot = ('+' in ua_string or
                      user_agents.parse(ua_string).is_bot or
                      'referer' not in flask.request.headers)

@app.errorhandler(werkzeug.exceptions.TooManyRequests)
def antibot(e):
    response = e.get_response()
    response.data = flask.render_template('gatekeep.html', sid=arrow.now().format('X'))
    return response

@app.errorhandler(werkzeug.exceptions.HTTPException)
def error_page(e):
    response = e.get_response()
    response.data = flask.render_template('error.html', error=e)
    return response

@app.route('/')
@app.route('/<string:tag>')
def flrig(tag=None):
    """ main page handler """
    LOGGER.debug("root %s", tag)

    if '&amp;' in flask.request.url:
        raise werkzeug.exceptions.BadRequest("learn how HTML entities work, you stupid bot")


    if tag:
        # check for a passed sentience check
        LOGGER.debug("checking sentience")
        try:
            sid, token = flask.session['sid']
            now = arrow.utcnow()
            LOGGER.debug("now=%s sid=%s", now, arrow.get(sid))
            LOGGER.debug("token=%s key=%s", token, keymaster(sid))
            if not (now.shift(hours=-1) < arrow.get(float(sid)) < now and
                keymaster(sid) == token):
                LOGGER.debug("session invalid")
                raise werkzeug.exceptions.TooManyRequests(retry_after=3600)
        except (KeyError, ValueError, arrow.ParserError) as e:
            LOGGER.debug("missing or malformed session: %s", e)
            raise werkzeug.exceptions.TooManyRequests(retry_after=3600)

    if tag and wordfilter.Wordfilter().blacklisted(tag):
        raise werkzeug.exceptions.NotFound("I don't know what that word means")

    return flask.render_template(
        'flrig.html',
        feed=get_feed(tag),
        tag=tag,
        filter_description=filter_description)


@app.route('/', methods=["POST"])
@app.route('/<string:tag>', methods=["POST"])
def gatekeep(tag=None):
    """ handle potential AI bots """
    try:
        sid = float(flask.request.form['sid'])
    except ValueError:
        raise werkzeug.exceptions.BadRequest("invalid token")

    now = arrow.now()

    if arrow.get(sid) > now:
        raise werkzeug.exceptions.BadRequest("hello time traveler")
    if arrow.get(sid) < now.shift(minutes=-15):
        raise werkzeug.exceptions.TooManyRequests(retry_after=3600)

    flask.session['sid'] = (sid, keymaster(sid))
    return flask.redirect(flask.url_for('flrig', tag=tag))


@app.route('/robots.txt')
def robots_txt():
    """ robots.txt handler """
    return flask.send_file('robots.txt')

@app.route('/favicon.ico')
def favicon():
    """ favicon handler """
    return 'nope', 404


app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

if __name__ == '__main__':
    app.run(debug=True)
