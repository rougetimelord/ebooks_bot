import markov
import tweepy
import json

class Bot():
    def __init__(self):
        try:
            with open('data.json', 'r') as f:
                self.data = json.load(f)
                self.done = self.data['done']
                self.base = self.data['base']
                #import keys
        except IOError:
            self.data = {}
            self.done = []
            self.base = input('What account is your ebook based on?')
        self.api = self.connect()
        self.chain = markov.Chain()

    def dump(self):
        self.data = {'done': self.done, 'base': self.base}
        try:
            with open('data.json', 'w') as f:
                json.dump(self.data, f)
        except IOError:
            with open('data.json', 'w+') as f:
                json.dump(self.data, f)

    def connect(self):
        return '' #connect to twitter api and return api object here

    def add_tweets(self, tweets):
        for tweet in tweets:
            tweet_id = tweet.id_str
            if not tweet_id in self.done:
                self.chain.add_text(tweet.full_text)
                self.done.append(tweet_id)

    def start(self):
        if(self.chain.status):
            #add only new tweets
            return ''
        else:
            #add all account tweets
            return ''


if __name__ == "__main__":
    bot = Bot()
    bot.start()
