import markov
import tweepy
import json, re, random, time

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
                #import keys
        except IOError:
            self.data = {}
            self.done = []
            self.base = input('What account is your ebook based on? ')
            self.keys = {'con_k': input('Consumer key '), 'con_s': input('Consumer secret ')}
            self.dump()
        self.api = self.connect()
        self.chain = markov.Chain()

    def dump(self):
        self.data = {'done': self.done, 'base': self.base, 'keys': self.keys}
        try:
            with open('data.json', 'w') as f:
                json.dump(self.data, f)
        except IOError:
            with open('data.json', 'w+') as f:
                json.dump(self.data, f)

    def connect(self):
        auth = tweepy.OAuthHandler(self.keys['con_k'], self.keys['con_s'])
        if 'acc_k' in self.keys and 'acc_s' in self.keys:
            auth.set_access_token(self.keys['acc_k'], self.keys['acc_s'])
        else:
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
        return tweepy.API(auth)

    def post_tweet(self):
        text = self.chain.generate_text(random.randint(30, 140))
        self.api.update_status(status=text)

    def add_tweets(self, tweets):
        for tweet in tweets:
            if not tweet.id_str in self.done and not tweet.retweeted_status:
                if tweet.extended_text:
                    text = uni_norm(tweet.extended_tweet.full_text)
                else:
                    text = uni_norm(tweet.full_text)
                text = re.sub(r'(http)[a-zA-z:\/.]*', '', text)
                self.chain.add_text(text)
                self.done.append(tweet.id_str)

    def get_all_tweets(self):
        all_tweets = []
        next_tweets = self.api.user_timeline(screen_name=self.base, count=200, include_rts='false')
        all_tweets.extend(next_tweets)
        old_id = all_tweets[-1].id - 1
        while len(next_tweets) > 0:
            next_tweets = self.api.user_timeline(screen_name=self.base, count=200, include_rts='false',max_id=old_id)
            all_tweets.extend(next_tweets)
            old_id = all_tweets[-1].id - 1
        self.add_tweets(all_tweets)

    def start(self):
        if not self.chain.status:
            self.get_all_tweets()
        self.listener = StreamList()
        self.stream = tweepy.Stream(self.api.auth, self.listener)
        self.stream.filter(follow=[self.base], async_=True)
        while True:
            self.post_tweet()
            time.sleep(random.randint(6.0E1, 3.6E3))

class StreamList(tweepy.StreamListener):
    def on_status(self, status):
        BOT.add_tweets([status])

if __name__ == "__main__":
    BOT = Bot()
    BOT.start()
