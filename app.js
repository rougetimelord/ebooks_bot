var url = new URL(window.location);
var key = url.searchParams.get('oauth_token')
document.addEventListener('DOMContentLoaded', ()=>{document.getElementById('key').innerText=key})