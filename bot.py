#bot.py, a manager of interactions with the twitter api
#Copyright (C) 2018 Blair "rouge" LaCriox
import markov
import tweepy
import json, re, random, time, threading
from html import unescape

def uni_norm(text):
    return text.translate({0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                          0xa0:0x20})

class Bot():
    def __init__(self):
        print("Initiating bot")
        self.lock = threading.Lock()
        try:
            with open('data.json', 'r') as f:
                self.data = json.load(f)
                self.done = self.data['done']
                self.base = self.data['base']
                self.keys = self.data['keys']
                self.last_reply = self.data['last_reply']
                self.last_id = self.data['last_id']
                self.uid = self.data['uid']
        except IOError:
            self.data = {}
            self.done = []
            self.base = input('What account is your ebook based on? ')
            self.keys = {'con_k': input('Consumer key '), 'con_s': input('Consumer secret ')}
            self.last_reply = 1
            self.last_id = 1
            self.uid = 0
            self.dump()
        self.api = self.connect()
        if self.uid == 0:
            self.uid = self.api.lookup_users(screen_names=[self.base])[0].id
        self.chain = markov.Chain()
        self.ignore = [r'[ |\.]?(@[A-Za-z0-9_]{1,15})', r' ?(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*', r' ?#[a-zA-Z0-9_]*', r' ?\$[A-Za-z]{1,6}', r' ?…', r' ?pic.twitter.com[A-Za-z\/0-9]*',r' ?" ?',r'(?<= ) {1,}',r'( -(?=[a-zA-Z]))|((?<=[a-zA-Z])- )', r'^ ']

    def dump(self):
        print("Dumping json from bot")
        #dump json data to file, thread safely
        self.lock.acquire()
        self.data = {'done': self.done, 'base': self.base, 'keys': self.keys, 'last_reply': self.last_reply, 'last_id': self.last_id, 'uid': self.uid}
        try:
            with open('data.json', 'w') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        except IOError:
            with open('data.json', 'w+') as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        self.lock.release()

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
                print('Failed to get request token, exitting')
                exit()
            verifier = input('Verifier: ')
            try:
                auth.get_access_token(verifier)
            except tweepy.TweepError:
                print('Failed to get access token, exitting')
                exit()
            self.keys['acc_k'] = auth.access_token
            self.keys['acc_s'] = auth.access_token_secret
            self.dump()
        return tweepy.API(auth)

    def add_tweets(self, tweets):
        print("Adding tweets")
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
                for char in [':', ';', '.', '?', '!', ',']:
                    pat = re.escape(char) + r'{2,}'
                    text = re.sub(pat, char, text)
                if not len(text) == 0:
                    if not text[-1] in [':', ';', '.', '?', '!', ',']:
                        text += '.'
                    self.chain.add_text(text)
                self.done.append(tweet.id_str)
        self.dump()

    def get_tweets(self):
        print("Getting tweets")
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
            print('Getting tweets failed with %s' % e)

    def post_reply(self, orig_id):
        print("Posting a reply")
        #post a reply to a mention
        text = self.chain.generate_text(random.randint(30, 140))
        try:
            self.api.update_status(status=text, in_reply_to_status_id=orig_id, auto_populate_reply_metadata=True)
        except tweepy.TweepError as e:
            print('Failed to post reply with %s' % e)

    def check_mentions(self):
        print("Checking mentions")
        #check for the last 20 mentions since the last check, then reply
        mentions = self.api.mentions_timeline(since_id=self.last_reply)
        for tweet in mentions:
            self.last_reply = tweet.id
            self.post_reply(tweet.id)
    
    def mentions_wrapper(self):
        while True:
            self.check_mentions()
            self.dump()
            time.sleep(3.0E2)

    def post_tweet(self):
        print("Posting a tweet")
        #post a generated tweet
        text = self.chain.generate_text(random.randint(30, 140))
        try:
            self.api.update_status(status=text)
        except tweepy.TweepError as e:
            print('Failed to post tweet with %s' % e)

    def post_wrapper(self):
        while True:
            self.post_tweet()
            wait = random.randint(3.0E2, 3.6E3)
            print("Waiting %s minutes until next post" % round(wait/60, 2))
            time.sleep(wait)

    def start(self):
        print("Starting bot")
        self.get_tweets()
        #set up an event listener for base account tweets
        self.listener = StreamList(self)
        self.stream = tweepy.Stream(self.api.auth, self.listener)
        self.stream.filter(follow=[str(self.uid)], async_=True)
        #create threads for posting and mentions
        self.post_thread = threading.Thread(target=self.post_wrapper, name='Post_Thread')
        self.mention_thread = threading.Thread(target=self.mentions_wrapper, name='Mention_Thread')
        self.post_thread.start()
        self.mention_thread.start()
        self.post_thread.join()
        self.mention_thread.join()

class StreamList(tweepy.StreamListener):
    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    def on_status(self, status):
        self.bot.last_id = status.id
        self.bot.add_tweets([status])

if __name__ == "__main__":
    #create bot instance and start it
    BOT = Bot()
    BOT.start()
