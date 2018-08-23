import markov
import tweepy
import json, re, random, time, threading

def uni_norm(text):
    return text.translate({0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                          0xa0:0x20})

class Bot():
    def __init__(self):
        try:
            with open('data.json', 'r') as f:
                self.data = json.load(f)
                self.done = self.data['done']
                self.base = self.data['base']
                self.keys = self.data['keys']
                self.last_reply = self.data['last_reply']
                self.last_id = self.data['last_id']
        except IOError:
            self.data = {}
            self.done = []
            self.base = input('What account is your ebook based on? ')
            self.keys = {'con_k': input('Consumer key '), 'con_s': input('Consumer secret ')}
            self.last_reply = 0
            self.last_id = 0
            self.dump()
        self.api = self.connect()
        self.chain = markov.Chain()
        self.lock = threading.Lock()
        self.ignore = [r'\.?(@[A-Za-z0-9_]{1,15})', r'(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*', r'#[a-zA-Z0-9_]*', r'\$[A-Za-z]{1,6}', r'…', r'pic.twitter.com[A-Za-z\/0-9]*',r'"',r'(?<= ) {1,}']

    def dump(self):
        #dump json data to file, thread safely
        self.lock.acquire()
        self.data = {'done': self.done, 'base': self.base, 'keys': self.keys, 'last_reply': self.last_reply}
        try:
            with open('data.json', 'w') as f:
                json.dump(self.data, f)
        except IOError:
            with open('data.json', 'w+') as f:
                json.dump(self.data, f)
        self.lock.release()

    def connect(self):
        #connect to twitter api
        auth = tweepy.OAuthHandler(self.keys['con_k'], self.keys['con_s'])
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
            self.keys['acc_k': auth.access_token, 'acc_s': auth.access_token_secret]
            self.dump()
        return tweepy.API(auth)

    def add_tweets(self, tweets):
        #add tweets from the base account to the markov chain
        for tweet in tweets:
            if not tweet.id_str in self.done and not tweet.retweeted_status:
                if tweet.extended_text:
                    text = uni_norm(tweet.extended_tweet.full_text)
                else:
                    text = uni_norm(tweet.full_text)
                for pat in self.ignore:
                    text = re.sub(pat, '', text)
                for char in [':', ';', '.', '?', '!', ',']:
                    pat = re.escape(char) + r'{2,}'
                    text = re.sub(pat, char, text)
                self.chain.add_text(text)
                self.done.append(tweet.id_str)
        self.dump()

    def get_tweets(self):
        #get every tweet, since last start up, or get every tweet
        all_tweets = []
        try:
            next_tweets = self.api.user_timeline(screen_name=self.base, count=200,
                                                include_rts='false', since_id=self.last_id)
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
        #post a reply to a mention
        text = self.chain.generate_text(random.randint(30, 140))
        try:
            self.api.update_status(status=text, in_reply_to_status_id=orig_id, auto_populate_reply_metadata=True)
        except tweepy.TweepError as e:
            print('Failed to post reply with %s' % e)

    def check_mentions(self):
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
        #post a generated tweet
        text = self.chain.generate_text(random.randint(30, 140))
        try:
            self.api.update_status(status=text)
        except tweepy.TweepError as e:
            print('Failed to post tweet with %s' % e)

    def post_wrapper(self):
        while True:
            self.post_tweet()
            time.sleep(random.randint(6.0E1, 3.6E3))

    def start(self):
        self.get_tweets()
        #set up an event listener for base account tweets
        self.listener = StreamList()
        self.stream = tweepy.Stream(self.api.auth, self.listener)
        self.stream.filter(follow=[self.base], async_=True)
        #create threads for posting and mentions
        self.post_thread = threading.Thread(target=self.post_wrapper, name='Post_Thread')
        self.mention_thread = threading.Thread(target=self.mentions_wrapper, name='Mention_Thread')
        self.post_thread.run()
        self.mention_thread.run()
        self.post_thread.join()
        self.mention_thread.join()

class StreamList(tweepy.StreamListener):
    def on_status(self, status):
        BOT.last_id = status.id
        BOT.add_tweets([status])

if __name__ == "__main__":
    #create bot instance and start it
    BOT = Bot()
    BOT.start()
