# Scrapes every tweet from the user, not just the last 3200.
# You should run retrain.py before using this
import datetime, json, math, re
from html import unescape
from time import sleep
import tweepy
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.keys import Keys
import Markov

# Configurable options
delay = 2  # time to wait on each page load before reading the page
driver = webdriver.Chrome()  # options are Chrome() Firefox() Safari()

try:
    with open("data.json") as f:
        data = json.load(f)
except IOError as e:
    print(e)
    exit()

print("Connecting to Twitter API")
# connect to twitter api
auth = tweepy.OAuthHandler(
    data["keys"]["con_k"], data["keys"]["con_s"], "https://auth.r0uge.org",
)
if "acc_k" in data["keys"] and "acc_s" in data["keys"]:
    auth.set_access_token(data["keys"]["acc_k"], data["keys"]["acc_s"])
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
    data["keys"]["acc_k"] = auth.access_token
    data["keys"]["acc_s"] = auth.access_token_secret
api = tweepy.API(auth)

start = api.get_user(id=data["uid"]).created_at
end = datetime.datetime.now()

days = (end - start).days + 1
tweet_selector = "article > div > div > div:nth-child(2) > div > div:nth-child(1) > div > div > div > a"
user = data["base"].lower()
ids = []


def format_day(date):
    day = "0" + str(date.day) if len(str(date.day)) == 1 else str(date.day)
    month = "0" + str(date.month) if len(str(date.month)) == 1 else str(date.month)
    year = str(date.year)
    return "-".join([year, month, day])


def form_url(since, until):
    p1 = "https://twitter.com/search?f=tweets&vertical=default&q=from%3A"
    p2 = (
        user
        + "%20since%3A"
        + since
        + "%20until%3A"
        + until
        + "include%3Aretweets&src=typd"
    )
    return p1 + p2


def increment_day(date, i):
    return date + datetime.timedelta(days=i)


# Search every two month period
for day in range(math.ceil(days / 60)):
    d1 = format_day(increment_day(start, 0))
    d2 = format_day(increment_day(start, 60))
    url = form_url(d1, d2)
    driver.get(url)
    sleep(delay)
    try:
        found_tweets = driver.find_elements_by_css_selector(tweet_selector)
        all_tweets = found_tweets[:]
        increment = 0
        # Get all of the ids out of the links
        for tweet in all_tweets:
            try:
                id = tweet.get_attribute("href").split("/")[-1]
                ids.append(id)
            except StaleElementReferenceException as e:
                print("lost element reference", tweet)

        while len(found_tweets) >= increment:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(delay)

            found_tweets = driver.find_elements_by_css_selector(tweet_selector)
            all_tweets = found_tweets[:]
            for tweet in all_tweets:
                try:
                    id = tweet.get_attribute("href").split("/")[-1]
                    ids.append(id)
                except StaleElementReferenceException as e:
                    print("lost element reference", tweet)
            print("{} total ids".format(len(ids)))
            increment += 10
            sleep(delay)

    except NoSuchElementException:
        print("no tweets on this day")
    start = increment_day(start, 60)

print("done getting tweet ids")
driver.close()

final_ids = list(set(ids))
final_ids = [int(i) for i in final_ids]
print("Final number of ids : %s".format(len(final_ids)))


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def uni_norm(text):
    text = text.translate(
        {0x2018: 0x27, 0x2019: 0x27, 0x201C: 0x22, 0x201D: 0x22, 0xA0: 0x20}
    )
    return unescape(text)


chain = Markov.Chain()

ignore = [
    r"[ |\.]?(@[A-Za-z0-9_]{1,15})(?![A-Z0-9a-z])",
    r" ?(https?|www)[A-Za-z0-9:\/\.\-_?=%@~\+]*",
    r" ?\$[A-Za-z]{1,6}(?![A-Za-z])",
    r'(?<=\s)"\s',
    r"(?<= ) {1,}",
    r"^ ",
    r'"',
]


def add_tweets(tweets):
    """Adds new tweets to the Markov chain.

        Arguments:
            tweets {list} -- A list of tweets gotten.
        """

    print("Adding %s tweet(s)" % len(tweets))
    # add tweets from the base account to the markov chain
    for tweet in tweets:
        text = "\x02"
        if tweet.truncated:
            text += uni_norm(tweet.extended_tweet["full_text"])
        elif hasattr(tweet, "full_text"):
            text += uni_norm(tweet.full_text)
        else:
            text += uni_norm(tweet.text)
        for pat in ignore:
            text = re.sub(pat, "", text)
        text = re.sub(r"\n{2,}", "\n", text)
        if not len(text) <= 1:
            text += "\x03"
            chain.add_text(text)


for ids_part in list(chunks(final_ids, 100)):
    tweets = api.statuses_lookup(ids_part, tweet_mode="extended")
    add_tweets(tweets)

with open("data.json", "w") as f:
    data["last_id"] = max(final_ids)
    json.dump(data, f, indent=4, sort_keys=True)

print("done")
