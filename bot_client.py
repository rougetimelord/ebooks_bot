import json, threading, re, random, time
import os
import markov, helper
from html import unescape

class Bot():
    def __init__(self):

        print("Initiating bot uwu")
        self.lock = threading.Lock()
        self.json_lock = threading.Lock()

        try:
            with open("data.json", "r") as f:
                self.data = json.load(f)

                self.base_addr = self.data['base_addr']
                self.auth_url = self.base_addr + "/auth/authorize.json"
                self.callback_url = self.base_addr + "/auth/callback.json"
                self.post_url = self.base_addr + "/post/tweet.json"
                self.reply_url = self.base_addr + "/post/reply.json"
                self.tweets_url = self.base_addr + '/user/tweets.json'

                self.keys = self.data['keys']
                self.base = self.data['base']
                self.last_reply = self.data['last_reply']
                self.last_id = self.data['last_id']
                self.wait = self.data['wait']
        except IOError:
            self.data = {}
            self.keys = {}

            self.base_addr = input("Alias server url?? ")
            self.auth_url = self.base_addr + "/auth/authorize.json"
            self.callback_url = self.base_addr + "/auth/callback.json"
            self.post_url = self.base_addr + "/post/tweet.json"
            self.reply_url = self.base_addr + "/post/reply.json"
            self.tweets_url = self.base_addr + '/user/tweets.json'

            self.base = input("Base account: ")
            self.last_id = 1
            self.last_reply = 1
            self.wait = 0
            
            self.authorize()
            self.dump()
        
        self.chain = markov.Chain()
        #This really long regex array filters out tags, websites, tickers,
        #weird quotes, long white space, and beginning spaces.
        self.ignore = [r'[ |\.]?(@[A-Za-z0-9_]{1,15})(?![A-Z0-9a-z])', r' ?(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*', r' ?\$[A-Za-z]{1,6}(?![A-Za-z])',r'(?<=\s)"\s',r'(?<= ) {1,}', r'^ ', r'"']

    def authorize(self):
        response = helper.make_request(self.auth_url, {}, "GET")
        if 'errors' in response:
            print(response['errors'])
            exit()
        print("Go to: %s" % response['url'])
        verifier = input("Verifier: ")
        oauth_token = input("OAuth token: ")

        response = helper.make_request(self.callback_url, {
            'oauth_verifier': verifier,
            'oauth_token': oauth_token
        }, "GET")
        if 'errors' in response:
            print(response['errors'])
            exit()
        self.keys = {
            'token': response['token'], 'secret': response['secret']}
        return
                
    def dump(self, silent=False):
        if not silent:
            print("dumping json to disk")
        self.lock.acquire()
        self.data = {'base':self.base,'keys':self.keys,'last_reply':self.last_reply,'last_id':self.last_id,'base_addr':self.base_addr,'wait':self.wait}
        try:
            os.remove("data.json")
        except OSError:
            pass
        with open("data.json", "w+") as f:
            json.dump(self.data, f, indent=4, sort_keys=True)
        self.lock.release()
        return

    def add_tweets(self, tweets):
        print("Adding %s tweet(s)" % len(tweets))
        self.json_lock.acquire()
        for tweet in tweets:
            if not "retweeted_status" in tweet:
                text = "\x02"
                if "extended_tweet" in tweet:
                    text_temp = unescape(tweet['extended_tweet']['full_tweet'])
                    text += helper.uni_norm(text_temp)
                else:
                    text_temp = unescape(tweet['text'])
                    text += helper.uni_norm(text_temp)
                for pat in self.ignore:
                    text = re.sub(pat, '', text)
                text = re.sub(r'\n{2,}', '\n', text)
                if not len(text) == 1:
                    text += '\x03'
                    self.chain.add_text(text)
        self.json_lock.release()
        print("Done adding tweets uwu")
        self.dump()
        return

    def get_tweets(self):
        all_tweets = []
        next_tweets = helper.make_request(self.tweets_url, {
            'oauth_token': self.keys['token'],
            'oauth_secret': self.keys['secret'],
            'since_id': self.last_id,
            'screen_name': self.base
        }, "GET")

        if len(next_tweets) == 0:
            return
        all_tweets.extend(next_tweets)
        max_id = all_tweets[-1]['id'] - 1
        min_id = self.last_id
        self.last_id = all_tweets[0]['id']
        while len(next_tweets) > 0:
            next_tweets = next_tweets = helper.make_request(
                                            self.tweets_url, {
                                                'oauth_token': self.keys['token'],
                                                'oauth_secret': self.keys['secret'],
                                                'since_id': min_id,
                                                'max_id': max_id,
                                                'screen_name': self.base
                                            }, "GET")
            all_tweets.extend(next_tweets)
            max_id = all_tweets[-1]['id'] - 1
        self.dump(silent=True)
        self.add_tweets(all_tweets)
        return

    def post_tweet(self):
        print("Posting tweets")
        self.json_lock.acquire()
        text = self.chain.generate_text(random.randint(1,5))
        resp = helper.make_request(self.post_url, {'oauth_token': self.keys['token'],
                                                'oauth_secret': self.keys['secret'],
                                                'status': text
                                                }, "POST")
        if 'errors' in resp:
            print(resp['errors'])
        else:
            print("Posted")
        self.json_lock.release()
        return
    
    def sleep_wrapper(self):
        time_wait = int(self.wait)
        for _ in range (0, time_wait):
            time.sleep(1)
            self.wait -= 1
            if self.wait % 60 == 0:
                self.dump(silent=True)
        return
    
    def post_wrapper(self):
        """Wraps tweet posting so that it can be on it's own thread.
        """

        if not self.wait == 0:
            self.sleep_wrapper()
        while True:
            self.post_tweet()
            self.wait = 3.6E3
            print("Waiting %s minutes until next post" % round(self.wait/60, 2))
            self.sleep_wrapper()
        return

    def start(self):
        print("Starting bot")
        if not self.wait == 0:
            print("Waiting %s minutes b4 posting" % round(self.wait / 60, 2))
        self.get_tweets()
        #self.post_thread = threading.Thread(target=self.post_wrapper, name="Post_Thread")
        #self.post_thread.start()
        return

if __name__ == "__main__":
    bot = Bot()
    bot.start()