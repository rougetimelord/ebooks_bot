#bot.py, a manager of interactions with the twitter api
#Copyright (C) 2018 Blair "rouge" LaCriox
import markov
import tweepy
import json, re, random, time, threading
from html import unescape
import urllib.error as URL_Error
import urllib.request as request

def uni_norm(text):
    return text.translate({0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                          0xa0:0x20})

class Bot():
    """Inisiate bot by loading JSON, setting a lock and connecting to the API.
    """

    def __init__(self):
        print("Initiating bot uwu")
        self.lock = threading.Lock()
        self.json_lock = threading.Lock()
        try:
            with open('data.json', 'r') as f:
                self.data = json.load(f)
                self.done = self.data['done']
                self.base = self.data['base']
                self.keys = self.data['keys']
                self.last_reply = self.data['last_reply']
                self.last_id = self.data['last_id']
                self.uid = self.data['uid']
                self.wait = self.data['wait']
        except IOError:
            self.data = {}
            self.done = []
            self.base = input('What account is your ebook based on? ')
            self.keys = {'con_k': input('Consumer key '), 'con_s': input('Consumer secret ')}
            self.last_reply = 1
            self.last_id = 1
            self.uid = 0
            self.wait = 0
            self.dump()
        self.api = self.connect()
        if self.uid == 0:
            self.uid = self.api.lookup_users(screen_names=[self.base])[0].id
        self.chain = markov.Chain()
        #This really long regex array filters out tags, websites, tickers,
        #weird quotes, long white space, and beginning spaces.
        self.ignore = [r'[ |\.]?(@[A-Za-z0-9_]{1,15})', r' ?(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*', r' ?\$[A-Za-z]{1,6}',r'(?<=\s)"\s',r'(?<= ) {1,}', r'^ ', r'"']

    """Dumps json data to file, thread safely.

    Arguments:
        silent: Determines whether there will output.

    """

    def dump(self, silent=False):
        if not silent:
            print("Dumping json from bot uwu")
        self.lock.acquire()
        #Truncate the list of done tweets as needed
        if len(self.done) > 200:
            self.done = self.done[-200:]
        
        self.data = {'done': self.done, 'base': self.base, 'keys': self.keys, 'last_reply': self.last_reply, 'last_id': self.last_id, 'uid': self.uid, 'wait': self.wait}
        try:
            with open('data.json', 'w') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        except IOError:
            with open('data.json', 'w+') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        self.lock.release()
        return

    """Connects the bot to the twitter api.
    
    Returns:
        tweepy.API: An instance of a twitter API connection.
    """

    def connect(self):
        print("Connecting to Twitter API")
        #connect to twitter api
        auth = tweepy.OAuthHandler(self.keys['con_k'], self.keys['con_s'], "https://auth.r0uge.org")
        if 'acc_k' in self.keys and 'acc_s' in self.keys:
            auth.set_access_token(self.keys['acc_k'], self.keys['acc_s'])
        else:
            #if an access token hasn't been generated yet, go through the process of getting one
            try:
                url = auth.get_authorization_url()
                print('Go to %s' % url)
            except tweepy.TweepError:
                print('Failed to get request token, exitting OWO')
                exit()
            verifier = input('Verifier: ')
            try:
                auth.get_access_token(verifier)
            except tweepy.TweepError:
                print('Failed to get access token, exitting OWO')
                exit()
            self.keys['acc_k'] = auth.access_token
            self.keys['acc_s'] = auth.access_token_secret
            self.dump()
        return tweepy.API(auth)

    """Pings a DNS to check if the device is online.

    Returns:
        Boolean -- Whether the device is connected to the internet.
    """

    def ping():
        try:
            req = request.Request(url="http://1.1.1.1",method="HEAD")
            with request.urlopen(req) as res:
                if res.status == 200:
                    return True
                else:
                    return False
        except URL_Error as e:
            return False

    """Adds new tweets to the Markov chain.
    """

    def add_tweets(self, tweets):
        print("Adding %s tweet(s)" % len(tweets))
        self.json_lock.acquire()
        #add tweets from the base account to the markov chain
        for tweet in tweets:
            if not tweet.id_str in self.done and not "retweeted_status" in tweet._json:
                if "extended_text" in tweet._json:
                    text = unescape(tweet.extended_tweet.full_text)
                    text = uni_norm(tweet.extended_tweet.full_text)
                else:
                    text = unescape(tweet.text)
                    text = uni_norm(text)
                for pat in self.ignore:
                    text = re.sub(pat, '', text)
                for char in [':', ';', '.', '?', '!', ',', "\n"]:
                    if (char == '\n'):
                        pat = char + r'{2,}'
                    else:
                        pat = re.escape(char) + r'{2,}'
                    text = re.sub(pat, char, text)
                if not len(text) == 0:
                    if not text[-1] in [':', ';', '.', '?', '!', ',', "\n"]:
                        text += '.'
                    self.chain.add_text(text)
                self.done.append(tweet.id_str)
        self.json_lock.release()
        self.dump()
        return

    """ Gets all of the base account's tweets.
    """

    def get_tweets(self):
        print("Getting tweets nwn")
        #get every tweet, since last start up, or get every tweet
        all_tweets = []
        try:
            next_tweets = self.api.user_timeline(screen_name=self.base, count=200,
                                                include_rts='false', since_id=self.last_id)
            if len(next_tweets) == 0:
                return
            all_tweets.extend(next_tweets)
            old_id = all_tweets[-1].id - 1
            last = old_id
            while len(next_tweets) > 0:
                next_tweets = self.api.user_timeline(screen_name=self.base, count=200,
                                                    include_rts='false',max_id=old_id,since_id=self.last_id)
                all_tweets.extend(next_tweets)
                old_id = all_tweets[-1].id - 1
            self.add_tweets(all_tweets)
            self.last_id = last + 1
        except tweepy.TweepError as e:
            print('Getting tweets failed with %s OWO' % e)
        return

    """Posts a reply if needed

    Args:
        orig_id: A string that is the tweet id of the tweet to reply to.
    """

    def post_reply(self, orig_id):
        print("Posting a reply uwu")
        #post a reply to a mention
        text = self.chain.generate_text(random.randint(30, 140))
        try:
            self.api.update_status(status=text, in_reply_to_status_id=orig_id, auto_populate_reply_metadata=True)
        except tweepy.TweepError as e:
            print('Failed to post reply with %s OWO' % e)
        except URL_Error.URLError as f:
            print("%s happened owo" % f)
            a = False
            while a == False:
                a = self.ping()
                time.sleep(60)
        return

    """Check if The bot has been mentioned and reply.
    """

    def check_mentions(self):
        print("Checking mentions")
        #check for the last 20 mentions since the last check, then reply
        mentions = self.api.mentions_timeline(since_id=self.last_reply)
        if len(mentions) != 0:
            print("Found %s mentions!" % len(mentions))
        else:
            print("No mentions uwu")
        for tweet in mentions:
            self.last_reply = tweet.id
            self.post_reply(tweet.id)
        return

    """Wraps the mention checker so it can be in it's own thread.
    """

    def mentions_wrapper(self):
        while True:
            self.check_mentions()
            self.dump()
            time.sleep(3.0E2)
        return

    """Wraps sleeping in a method that prints the JSON every minute.
    """

    def sleep_wrapper(self):
        time_wait = self.wait
        for i in range(time_wait):
            time.sleep(1)
            self.wait -= 1
            if self.wait % 60 == 0:
                self.dump(silent=True)
        return

    """Post a markov chain generated tweet.
    """

    def post_tweet(self):
        print("Posting a tweet")
        self.json_lock.acquire()
        #post a generated tweet
        text = self.chain.generate_text(random.randint(30, 140))
        try:
            self.api.update_status(status=text)
        except tweepy.TweepError as e:
            print('Failed to post tweet with %s OWO' % e)
        except URL_Error.URLError as f:
            print("%s happened owo" % f)
            a = False
            while a == False:
                a = self.ping()
                time.sleep(60)
        self.json_lock.release()
        return

    """Wraps tweet posting so that it can be on it's own thread.
    """

    def post_wrapper(self):
        if not self.wait == 0:
            self.sleep_wrapper()
        while True:
            self.post_tweet()
            self.wait = random.randint(3.0E2, 3.6E3)
            print("Waiting %s minutes until next post" % round(self.wait/60, 2))
            self.sleep_wrapper()
        return

    """Starts the stream listener.
    """

    def start_stream(self, wait=0):
        time.sleep(wait)
        #set up an event listener for base account tweets
        self.listener = StreamList(self)
        self.stream = tweepy.Stream(self.api.auth, self.listener)
        self.stream.filter(follow=[str(self.uid)], async_=True)
        return

    """Really starts up the bot.
    """

    def start(self):
        print("Starting bot")
        if not self.wait == 0:
            print('Waiting for %s minutes before tweeting uwu' % round(self.wait / 60, 2))
        self.get_tweets()
        self.start_stream()
        #create threads for posting and mentions
        self.post_thread = threading.Thread(target=self.post_wrapper, name='Post_Thread')
        self.mention_thread = threading.Thread(target=self.mentions_wrapper, name='Mention_Thread')
        self.post_thread.start()
        self.mention_thread.start()
        return

"""Manages the stream listener.
"""

class StreamList(tweepy.StreamListener):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    def on_status(self, status):
        self.bot.last_id = status.id
        self.bot.add_tweets([status])

    def on_connect(self):
        print("Stream connected uwu")

    def on_error(self, status_code):
        if status_code == 420:
            print("I need to chill TwT")
            self.bot.start_stream(60)
        else:
            print(status_code)
            self.bot.start_stream()
        return False


if __name__ == "__main__":
    #create bot instance and start it
    BOT = Bot()
    BOT.start()
