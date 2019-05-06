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

def uni_norm(text):
    return text.translate({0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                          0xa0:0x20})