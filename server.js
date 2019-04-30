// server.js
// where your node app starts

// init project
const express = require('express');
const app = express();
const session = require('cookie-session');
const OAuth = require('oauth').OAuth
const httpRequest = require('request');

require('dotenv').load();
var env = process.env;
const LoginWithTwitter = new (require('login-with-twitter'))({
  consumerKey: env.KEY_PUB,
  consumerSecret: env.KEY_SEC,
  callbackUrl: 'https://auth.r0uge.org' 
});

// we've started you off with Express, 
// but feel free to use whatever libs or frameworks you'd like through `package.json`.

// http://expressjs.com/en/starter/static-files.html
app.use(express.static('public'));
app.use(session({
  name: 'session',
  secret: 'bongocat',
  maxAge: 7 * 24 * 60 * 60 * 1000
}));

/* app.enable('trust proxy');
app.use((req, res, next) => {
  if(req.secure) {
    return next();
  }
  res.redirect('https://' + req.header.host + req.url);
}); */

app.get('/auth/authorize', (req, res) => {
  LoginWithTwitter.login((err, tokenSecret, url) => {
    if(err) {
      console.log(err);
      return next(err);
    }
    req.session.oauthSecret = tokenSecret;
    res.send({
      'url': url
    });
  });
});

app.get('/auth/callback', (req, res) => {
  console.log('Doing callback', req.query);
  LoginWithTwitter.callback({
    oauth_token: req.query.oauth_token,
    oauth_verifier: req.query.oauth_verifier
  }, req.session.oauthSecret, (err, user) => {
    if(err) {
      console.log('failed callback', err);
      res.send({
        'error': err
      });
      return;
    }
    delete req.session.oauthSecret;
    res.send({
      'token': user.userToken,
      'secret': user.userTokenSecret
    });
  });
});

app.get('/', (req, res) => {
  res.send('nothing here but us cats');
});

app.post('/post/reply', (req, res) => {
  res.send({'error': 'not implemented'})
})

app.post('/post/tweet', (req, res) => {
  let oauthHelper = new OAuth(
    'https://api.twitter.com/oauth/request_token',
    'https://api.twitter.com/oauth/access_token',
    env.KEY_PUB, env.KEY_SEC,
    '1.0', null, 'HMAC-SHA1'
  );

  let authHeader = oauthHelper.authHeader(
    "https://api.twitter.com/1.1/statuses/update.json?status=" + req.query.status,
    req.query.oauth_token, req.query.oauth_secret, 'POST'
  );

  let request = httpRequest.post({
    url: 'https://api.twitter.com/1.1/statuses/update.json?status=' + req.query.status,
    headers: {'Authorization': authHeader}
  }, (err, resp, body) => {
    if(err) {
      console.log(err);
      res.send(err);
      return;
    }
    res.send(JSON.parse(body));
  })
});

// listen for requests :)
const listener = app.listen(process.env.PORT, function() {
  console.log('Your app is listening on port ' + listener.address().port);
});