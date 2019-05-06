
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

app.get('/auth/authorize.json', (req, res) => {
  /**
   * Creates an app authorization url for the client.
   */
  LoginWithTwitter.login((err, tokenSecret, url) => {
    if(err) {
      console.log(err);
      return next(err);
    }
    //I don't have to hold on to the secret here but it's easiest.
    req.session.oauthSecret = tokenSecret;
    res.send({
      'url': url
    });
  });
});

app.get('/auth/callback.json', (req, res) => {
  /**
   * Handles the callback and gives the client an OAuth token.
   * 
   * I don't want it, so I don't hold on to it.
   */
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

app.post('/post/reply.json', (req, res) => {
  /**
   * Posts a reply to a tweet.
   * 
   * Client must supply a message and a tweet id to reply to.
   */

  //Make sure everything we need got supplied
  let errMsg = {errors: []}
  if(!req.query.status || !req.query.reply_to_id){
    errMsg.errors.push({
      "code": 1.1,
      "message": "Request missing a status or a reply ID."
    });
  } else if(!req.query.oauth_token || !req.query.oauth_secret){
    errMsg.errors.push({
      "code": 0,
      "message": "Authentication info is incomplete."
    });
  }
  if(errMsg.errors.length !== 0){
    res.send(errMsg);
    return;
  }

  //Create a URI
  let uri = "https://api.twitter.com/1.1/statuses/update.json?status=" 
  uri += encodeURIComponent(req.query.status);
  uri += "&in_reply_to_status_id";
  uri += encodeURIComponent(req.query.reply_to_id);
  
  //Make a OAuth header for the request
  let oauthHelper = new OAuth(
    'https://api.twitter.com/oauth/request_token',
    'https://api.twitter.com/oauth/access_token',
    env.KEY_PUB, env.KEY_SEC,
    '1.0', null, 'HMAC-SHA1'
  );
  let authHeader = oauthHelper.authHeader(
    uri, req.query.oauth_token, req.query.oauth_secret, 'POST'
  );

  //Send the post request to twitter
  let request = httpRequest.post({
    uri: uri,
    headers: {'Authorization': authHeader}
  }, (err, resp, body) => {
    /**
     * Handle the response from twitter.
     */
    if(err) {
      console.log(err);
      res.send(err);
      return;
    }
    res.send(JSON.parse(body));
  })
})

app.post('/post/tweet.json', (req, res) => {
  /**
   * Posts a new tweet.
   * 
   * Client must supply a message to post.
   */

  //Check if everything was supplied
  let errMsg = {errors: []}
  if(!req.query.status){
    errMsg.errors.push({
      "code": 1,
      "message": "Request missing a status."
    });
  } else if(!req.query.oauth_token || !req.query.oauth_secret){
    errMsg.errors.push({
      "code": 0,
      "message": "Authentication info is incomplete."
    });
  }
  if(errMsg.errors.length !== 0){
    res.send(errMsg);
  }

  //Create the twitter API URI
  let uri = "https://api.twitter.com/1.1/statuses/update.json?status="; 
  uri += encodeURIComponent(req.query.status);
  
  //Create a auth header
  let oauthHelper = new OAuth(
    'https://api.twitter.com/oauth/request_token',
    'https://api.twitter.com/oauth/access_token',
    env.KEY_PUB, env.KEY_SEC,
    '1.0', null, 'HMAC-SHA1'
  );
  let authHeader = oauthHelper.authHeader(
    uri, req.query.oauth_token, req.query.oauth_secret, 'POST'
  );

  //Make the request to twitter
  let request = httpRequest.post({
    uri: uri,
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

app.get('/user/tweets.json', (req, res) => {
  /**
   * Gets tweets from a user.
   * 
   * Client must supply a user id and since id.
   */

  //Check if everything was supplied
  let errMsg = {errors: []}
  if(!req.query.user_id || !req.query.since_id){
    errMsg.errors.push({
      "code": 2,
      "message": "Request missing user id or a since id."
    });
  } else if(!req.query.oauth_token || !req.query.oauth_secret){
    errMsg.errors.push({
      "code": 0,
      "message": "Authentication info is incomplete."
    });
  }
  if(errMsg.errors.length !== 0){
    res.send(errMsg);
  }

  //Create the URI
  let uri = "https://api.twitter.com/1.1/statuses/user_timeline.json?";
  uri += "user_id="+req.query.user_id;
  uri += "&since_id="+req.query.since_id;
  uri += "&count=200&include_rts=false";

  //Make the auth header
  let oauthHelper = new OAuth(
    'https://api.twitter.com/oauth/request_token',
    'https://api.twitter.com/oauth/access_token',
    env.KEY_PUB, env.KEY_SEC,
    '1.0', null, 'HMAC-SHA1'
  );
  let authHeader = oauthHelper.authHeader(
    uri, req.query.oauth_token, req.query.oauth_secret, 'GET'
  );

  //Send off the request
  let request = httpRequest({
    uri: uri,
    headers: {'Authorization': authHeader},
    method: 'GET'
  }, (err, resp, body) => {
    if(err){
      console.log(err);
      res.send(err);
      return;
    }
    res.send(JSON.parse(body));
  });
})

// listen for requests :)
const listener = app.listen(process.env.PORT, function() {
  console.log('Your app is listening on port ' + listener.address().port);
});