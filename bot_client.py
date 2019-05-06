import json, threading, re, random, time
import os
import markov, helper

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
        })
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

    def get_tweets(self):
        all_tweets = []
        try:
            next_tweets = helper.make_request(self.tweets_url, {
                
            })

if __name__ == "__main__":
    bot = Bot()
    bot.start()