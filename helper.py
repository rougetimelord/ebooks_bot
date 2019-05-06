import urllib.request
import urllib.error
import json

def make_request(url, params, method):
    url += "?"
    for key in params:
        url += "%s=%s&" % (key, params[key])

    url = url[:-1]

    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req) as res:
            response = json.load(res.read())
            return response
    except urllib.error.URLError as e:
        print('Oops messed up with %s' % url)
        return {'errors': e}