# ebooks_bot

A python twitter bot to do what horse_ebooks does.

## Requirements
- tweepy (`pip install -r requirements.txt`)
- a set of Twitter API keys
- a Twitter account to post to (I mean you could run it on main but 🤷)

This project also includes a page to get the verifier token hosted at [auth.r0uge.org](https://auth.r0uge.org), located in the `gh-pages` branch of this repo

## Extended_Scrape
The Twitter API limits searching a user's timeline to the most recent 3200 tweets, if you want to get every single tweet you can use `Extended_Scrape.py.` It is much much slower than the normal scraping that is done, and requires selenium. I will try to maintain it but issues related to using this tool will be closed as out of scope.