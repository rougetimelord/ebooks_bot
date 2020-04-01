# bot.py, a manager of interactions with the twitter api
# Copyright (C) 2018 Blair "rouge" LaCriox
import Markov, Stream
import tweepy
import json, re, time, threading
from html import unescape
from urllib.error import URLError as URL_Error
import urllib.request as request
from datetime import datetime as date

VERSION = "1.1.5"


def uni_norm(text):
    text = text.translate(
        {0x2018: 0x27, 0x2019: 0x27, 0x201C: 0x22, 0x201D: 0x22, 0xA0: 0x20}
    )
    return unescape(text)


class Bot:
    def __init__(self):
        """Initiate bot by loading JSON, setting a lock and connecting to the API.
        """

        print("Initiating bot uwu")
        self.json_lock = threading.Lock()
        self.markov_lock = threading.Lock()
        try:
            with open("data.json", "r") as f:
                self.data = json.load(f)
        except IOError:
            self.data = {
                "base": input("What account is your ebook based on? "),
                "keys": {
                    "consumer_token": input("Consumer key "),
                    "consumer_secret": input("Consumer secret "),
                },
                "last_id": 1,
                "last_reply": 1,
                "uid": 0,
            }
            self.dump()
        self.api = self.connect()
        if self.data["uid"] == 0:
            try:
                self.data["uid"] = self.api.lookup_users(
                    screen_names=[self.data["base"]]
                )[0].id
            except tweepy.TweepError as e:
                print("Couldn't get uid twt")
                exit()
        d = date.now()
        self.wait = 3.6e3 - (60 * d.minute + d.second)
        self.chain = Markov.Chain()
        # This really long regex array filters out tags, websites, tickers,
        # weird quotes, long white space, and beginning spaces.
        self.ignore = [
            r"[ |\.]?(@[A-Za-z0-9_]{1,15})(?![A-Z0-9a-z])",
            r" ?(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*",
            r" ?\$[A-Za-z]{1,6}(?![A-Za-z])",
            r'(?<=\s)"\s',
            r"(?<= ) {1,}",
            r"^ ",
            r'"',
        ]

    def dump(self, silent=False):
        """Dumps json data to file, thread safely.

        Arguments:
            silent {Boolean} -- Determines whether there will output.
        """

        if not silent:
            print("Dumping json from bot uwu")
        self.json_lock.acquire()

        try:
            with open("data.json", "w") as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        except IOError:
            with open("data.json", "w+") as f:
                json.dump(self.data, f, indent=4, sort_keys=True)
        self.json_lock.release()
        return

    def connect(self):
        """Connects the bot to the twitter api.
    
        Returns:
            tweepy.API -- An instance of a twitter API connection.
        """

        print("Connecting to Twitter API")
        # connect to twitter api
        auth = tweepy.OAuthHandler(
            self.data["keys"]["consumer_token"],
            self.data["keys"]["consumer_secret"],
            "https://auth.r0uge.org",
        )
        if (
            "access_token" in self.data["keys"]
            and "access_secret" in self.data["keys"]
        ):
            auth.set_access_token(
                self.data["keys"]["access_token"],
                self.data["keys"]["access_secret"],
            )
        else:
            # if an access token hasn't been generated yet, go through the process of getting one
            try:
                url = auth.get_authorization_url()
                print("Go to %s" % url)
            except tweepy.TweepError:
                print("Failed to get request token, exitting OWO")
                exit()
            verifier = input("Verifier: ")
            try:
                auth.get_access_token(verifier)
            except tweepy.TweepError:
                print("Failed to get access token, exitting OWO")
                exit()
            self.data["keys"]["access_token"] = auth.access_token
            self.data["keys"]["access_secret"] = auth.access_token_secret
            self.dump()
        return tweepy.API(auth)

    def add_tweets(self, tweets):
        """Adds new tweets to the Markov chain.

        Arguments:
            tweets {list} -- A list of tweets gotten.
        """

        print("Adding %s tweet(s) nwn" % len(tweets))
        self.markov_lock.acquire()
        # add tweets from the base account to the markov chain
        for tweet in tweets:
            if tweet.author.id == self.data["uid"]:
                text = "\x02"
                if tweet.truncated:
                    text += uni_norm(tweet.extended_tweet["full_text"])
                elif hasattr(tweet, "full_text"):
                    text += uni_norm(tweet.full_text)
                else:
                    text += uni_norm(tweet.text)
                for pat in self.ignore:
                    text = re.sub(pat, "", text)
                text = re.sub(r"\n{2,}", "\n", text)
                if not len(text) <= 1:
                    text += "\x03"
                    self.chain.add_text(text)
        self.markov_lock.release()
        print("Done adding tweets uwu")
        self.dump()
        return

    def get_tweets(self):
        """ Gets all of the base account's tweets.
        """

        print("Getting tweets nwn")
        # get every tweet, since last start up, or get every tweet
        all_tweets = []
        try:
            next_tweets = self.api.user_timeline(
                screen_name=self.data["base"],
                count=200,
                include_rts="false",
                since_id=self.data["last_id"],
                tweet_mode="extended",
            )
            if len(next_tweets) == 0:
                return
            all_tweets.extend(next_tweets)

            min_id = self.data["last_id"]
            self.data["last_id"] = all_tweets[0].id
            max_id = self.data["last_id"] - 1
            while len(next_tweets) > 0:
                next_tweets = self.api.user_timeline(
                    screen_name=self.data["base"],
                    count=200,
                    include_rts="false",
                    max_id=max_id,
                    since_id=min_id,
                    tweet_mode="extended",
                )
                all_tweets.extend(next_tweets)
                max_id = all_tweets[-1].id - 1
            self.dump(silent=True)
            self.add_tweets(all_tweets)
        except tweepy.TweepError as e:
            print("Getting tweets failed with %s OWO" % e)
        return

    def post_reply(self, orig_id):
        """Posts a reply if needed

        Arguments:
            orig_id {str} -- A string that is the tweet id of the tweet to \
                    reply to.
        """
        print("Posting a reply uwu")
        # post a reply to a mention
        text = self.chain.generate_text(1)
        try:
            self.api.update_status(
                status=text,
                in_reply_to_status_id=orig_id,
                auto_populate_reply_metadata=True,
            )
        except tweepy.TweepError as e:
            print("Failed to post reply with %s OWO" % e)
        except URL_Error as f:
            print("%s happened owo" % f)
        return

    def check_mentions(self):
        """Check if The bot has been mentioned and reply.
        """

        print("Checking mentions")
        try:
            # check for the last 20 mentions since the last check, then reply
            mentions = self.api.mentions_timeline(
                since_id=self.data["last_reply"]
            )
        except tweepy.TweepError as e:
            print("%s happened owo" % e)
            return
        if len(mentions) != 0:
            print("Found %s mentions!" % len(mentions))
        else:
            print("No mentions uwu")
            return

        # Skip posting on first start-up
        if self.data["last_id"] == 1:
            self.last_reply = mentions[0].id
            return

        # Grab the latest ID and post away
        self.data["last_reply"] = mentions[0].id
        for tweet in mentions:
            self.post_reply(tweet.id)
        return

    def mentions_wrapper(self):
        """Wraps the mention checker so it can be in it's own thread.
        """

        while True:
            self.check_mentions()
            self.dump()
            time.sleep(3.0e2)
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
        self.markov_lock.acquire()
        # post a generated tweet
        text = self.chain.generate_text(1)
        try:
            self.api.update_status(status=text)
        except tweepy.TweepError as e:
            print("Failed to post tweet with %s OWO" % e)
        except URL_Error as f:
            print("%s happened owo" % f)
        self.markov_lock.release()
        return

    def post_wrapper(self):
        """Wraps tweet posting so that it can be on it's own thread.
        """

        if not self.wait == 0:
            self.sleep_wrapper()
        while True:
            self.post_tweet()
            d = date.now()
            self.wait = 3.6e3 - (60 * d.minute + d.second)
            print(
                "Waiting %s minutes until next post" % round(self.wait / 60, 2)
            )
            self.sleep_wrapper()
        return

    def start_stream(self, wait=0):
        """Starts the stream listener
        
        Keyword Arguments:
            wait {int} -- How long to wait before starting. (default: {0})
        """

        time.sleep(wait)
        # set up an event listener for base account tweets
        self.listener = Stream.listener(self)
        self.stream = tweepy.Stream(self.api.auth, self.listener)
        self.stream.filter(follow=[str(self.data["uid"])], is_async=True)
        return

    def start(self):
        """Really starts up the bot.
        """

        print("Starting bot v" + VERSION)
        if not self.wait == 0:
            print(
                "Waiting for %s minutes before tweeting uwu"
                % round(self.wait / 60, 2)
            )
        self.get_tweets()
        self.start_stream()
        # create threads for posting and mentions
        self.post_thread = threading.Thread(
            target=self.post_wrapper, name="Post_Thread"
        )
        self.mention_thread = threading.Thread(
            target=self.mentions_wrapper, name="Mention_Thread"
        )
        self.post_thread.start()
        self.mention_thread.start()
        return


if __name__ == "__main__":
    # create bot instance and start it
    BOT = Bot()
    BOT.start()
