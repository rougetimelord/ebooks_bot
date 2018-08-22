var url_s = window.location;
var url = new URL(url_s);
var key = url.searchParams.get('oauth_token')
document.addEventListener('DOMContentLoaded', ()=>{document.getElementById('key').innerText=key})