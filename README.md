# ebooks_bot

A python twitter bot to do what horse_ebooks does.

## Requirements
- tweepy
    - if using python 3.7+ you will have to replace `async` in tweepy.stream with `async_`
    - otherwise change `async_` at `bot.py {134}` to `async`

This project also includes a page to get the verifier token hosted at [auth.r0uge.org](https://auth.r0uge.org), located in the `gh-pages` branch of this repo