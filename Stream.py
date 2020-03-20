import tweepy


class listener(tweepy.StreamListener):
    """Manages the stream listener.
    """

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api

    def on_status(self, status):
        """Reacts to new tweets and sends them off to the markov chain.
        
        Arguments:
            status {tweepy.Status} -- The tweet.
        """

        self.bot.last_id = status.id
        self.bot.add_tweets([status])

    def on_connect(self):
        """Alerts the user that the stream has been connected.
        """

        print("Stream connected uwu")

    def on_error(self, status_code):
        """Reacts to errors.
        
        Arguments:
            status_code {int} -- The error status code.
        
        Returns:
            Boolean -- Always false to close the listener.
        """

        if status_code == 420:
            print("I need to chill TwT")
            self.bot.start_stream(60)
        else:
            print(status_code)
            self.bot.start_stream()
        return False
