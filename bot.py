#bot.py, a manager of interactions with the twitter api
#Copyright (C) 2018 Blair "rouge" LaCriox
import markov, Stream
import tweepy
import json, re, random, time, threading
from html import unescape
from urllib.error import URLError as URL_Error
import urllib.request as request

def uni_norm(text):
    return text.translate({0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                          0xa0:0x20})

class Bot():
    def __init__(self):
        """Initiate bot by loading JSON, setting a lock and connecting to the API.
        """

        print("Initiating bot uwu")
        self.lock = threading.Lock()
        self.json_lock = threading.Lock()
        try:
            with open('data.json', 'r') as f:
                self.data = json.load(f)
                self.base = self.data['base']
                self.keys = self.data['keys']
                self.last_reply = self.data['last_reply']
                self.last_id = self.data['last_id']
                self.uid = self.data['uid']
                self.wait = self.data['wait']
        except IOError:
            self.data = {}
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
        self.ignore = [r'[ |\.]?(@[A-Za-z0-9_]{1,15})', r' ?(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*', r' ?\$[A-Za-z]{1,6}(?![A-Za-z])',r'(?<=\s)"\s',r'(?<= ) {1,}', r'^ ', r'"']

    def dump(self, silent=False):
        """Dumps json data to file, thread safely.

        Arguments:
            silent {Boolean} -- Determines whether there will output.
        """
        
        if not silent:
            print("Dumping json from bot uwu")
        self.lock.acquire()
        
        self.data = {'base': self.base, 'keys': self.keys, 'last_reply': self.last_reply, 'last_id': self.last_id, 'uid': self.uid, 'wait': self.wait}
        try:
            with open('data.json', 'w') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        except IOError:
            with open('data.json', 'w+') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        self.lock.release()
        return

    def connect(self):
        """Connects the bot to the twitter api.
    
        Returns:
            tweepy.API -- An instance of a twitter API connection.
        """

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

    def ping(self):
        """Pings a DNS to check if the device is online.

        Returns:
            Boolean -- Whether the device is connected to the internet.
        """

        try:
            print("Pinging 1.1.1.1 uwu")
            req = request.Request(url="http://1.1.1.1",method="HEAD")
            with request.urlopen(req) as res:
                if res.status == 200:
                    return True
                else:
                    return False
        except URL_Error:
            return False

    def add_tweets(self, tweets):
        """Adds new tweets to the Markov chain.

        Arguments:
            tweets {list} -- A list of tweets gotten.
        """

        print("Adding %s tweet(s) nwn" % len(tweets))
        self.json_lock.acquire()
        #add tweets from the base account to the markov chain
        for tweet in tweets:
            if not "retweeted_status" in tweet._json and not int(tweet.id_str) < self.last_id:
                if "extended_text" in tweet._json:
                    text = unescape(tweet.extended_tweet.full_text)
                    text = uni_norm(text)
                else:
                    text = unescape(tweet.text)
                    text = uni_norm(text)
                for pat in self.ignore:
                    text = re.sub(pat, '', text)
                pat = "\n" + r'{2,}'
                text = re.sub(pat, "\n", text)
                if not len(text) == 0:
                    text += "\03"
                    self.chain.add_text(text)
        self.json_lock.release()
        self.dump()
        return

    def get_tweets(self):
        """ Gets all of the base account's tweets.
        """

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
            self.last_id = last + 1
            self.dump(silent=True)
            self.add_tweets(all_tweets)
        except tweepy.TweepError as e:
            print('Getting tweets failed with %s OWO' % e)
        return

    def post_reply(self, orig_id):
        """Posts a reply if needed

        Arguments:
            orig_id {str} -- A string that is the tweet id of the tweet to \
                    reply to.
        """
        print("Posting a reply uwu")
        #post a reply to a mention
        text = self.chain.generate_text(random.randint(1, 3))
        try:
            self.api.update_status(status=text, in_reply_to_status_id=orig_id, auto_populate_reply_metadata=True)
        except tweepy.TweepError as e:
            print('Failed to post reply with %s OWO' % e)
        except URL_Error as f:
            print("%s happened owo" % f)
            a = False
            while a == False:
                a = self.ping()
                time.sleep(60)
        return

    def check_mentions(self):
        """Check if The bot has been mentioned and reply.
        """

        print("Checking mentions")
        #check for the last 20 mentions since the last check, then reply
        mentions = self.api.mentions_timeline(since_id=self.last_reply)
        if len(mentions) != 0:
            print("Found %s mentions!" % len(mentions))
        else:
            print("No mentions uwu")
            return

        if self.last_id == 1:
            self.last_reply = mentions[0].id
            return

        self.last_reply = mentions[0].id
        for tweet in mentions:
            self.last_reply = tweet.id
            self.post_reply(tweet.id)
        return

    def mentions_wrapper(self):
        """Wraps the mention checker so it can be in it's own thread.
        """

        while True:
            self.check_mentions()
            self.dump()
            time.sleep(3.0E2)
        return

    def sleep_wrapper(self):
        """Wraps sleeping in a method that prints the JSON every minute.
        """

        time_wait = int(self.wait)
        for _ in range(0, time_wait):
            time.sleep(1)
            self.wait -= 1
            if self.wait % 60 == 0:
                self.dump(silent=True)
        return

    def post_tweet(self):
        """Post a markov chain generated tweet.
        """

        print("Posting a tweet")
        self.json_lock.acquire()
        #post a generated tweet
        text = self.chain.generate_text(random.randint(1, 5))
        try:
            self.api.update_status(status=text)
        except tweepy.TweepError as e:
            print('Failed to post tweet with %s OWO' % e)
        except URL_Error as f:
            print("%s happened owo" % f)
            a = False
            while a == False:
                a = self.ping()
                time.sleep(60)
        self.json_lock.release()
        return

    def post_wrapper(self):
        """Wraps tweet posting so that it can be on it's own thread.
        """

        if not self.wait == 0:
            self.sleep_wrapper()
        while True:
            self.post_tweet()
            self.wait = 7.2E3
            print("Waiting %s minutes until next post" % round(self.wait/60, 2))
            self.sleep_wrapper()
        return

    def start_stream(self, wait=0):
        """Starts the stream listener
        
        Keyword Arguments:
            wait {int} -- How long to wait before starting. (default: {0})
        """


        time.sleep(wait)
        #set up an event listener for base account tweets
        self.listener = Stream.listener(self)
        self.stream = tweepy.Stream(self.api.auth, self.listener)
        self.stream.filter(follow=[str(self.uid)], is_async=True)
        return

    def start(self):
        """Really starts up the bot.
        """

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


if __name__ == "__main__":
    #create bot instance and start it
    BOT = Bot()
    BOT.start()
