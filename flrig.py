import flask
import feedparser
import requests

app = flask.Flask(__name__)


@app.route('/')
@app.route('/<string:tag>')
def flrig(tag=None):
    params = {'format': 'atom'}
    if tag:
        params['tag'] = tag

    req = requests.get(
        'http://api.flickr.com/services/feeds/photos_public.gne', params=params)
    feed = feedparser.parse(req.text)

    return flask.render_template('flrig.html', feed=feed, tag=tag)

if __name__ == '__main__':
    app.run()
