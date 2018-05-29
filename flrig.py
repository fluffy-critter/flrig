import flask
import feedparser
import requests
import re

app = flask.Flask(__name__)


def print_license(url):
    cc = re.search(r'licenses/(.*)/deed', url)
    if cc:
        return flask.Markup('''
<a href="{url}"><img src="https://licensebuttons.net/l/{license}/88x31.png" title="Creative Commons {license}" alt="{license}"> Creative Commons {license}</a>
'''.format(url=url, license=cc.group(1)))

    if 'publicdomain' in url:
        return flask.Markup('''<a href="{url}">Public domain</a>'''.format(url=url))

    return flask.Markup('<a href="{url}">unrecognized license</a>'.format(url=url))


def get_feed(tag=None):
    params = {'format': 'atom'}
    if tag:
        params['tag'] = tag

    req = requests.get(
        'http://api.flickr.com/services/feeds/photos_public.gne', params=params)
    feed = feedparser.parse(req.text)

    return feed


@app.route('/')
@app.route('/<string:tag>')
def flrig(tag=None):
    return flask.render_template('flrig.html', feed=get_feed(tag), tag=tag, print_license=print_license)

if __name__ == '__main__':
    app.run(debug=True)
