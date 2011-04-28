import oauth2 as oauth
import cgi
import json
from myproject.readability import *

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from myproject.models import UserProfile
from django.template import RequestContext

consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
client = oauth.Client(consumer)

def readability_login(request):
    if 'username' in request.GET:
        username = request.GET['username']
        u = User.objects.get(username__exact=username)
   
        user = authenticate(username=username, 
                password=u.get_profile().oauth_secret)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/profile/' + username)
                # Redirect to a success page.
            else:
                print 'error!'
                # Return a 'disabled account' error message
        else:
            print 'error!'
            # Return an 'invalid login' error message.

    resp, content = client.request(REQUEST_TOKEN_URL, "GET")
    if resp['status'] != '200':
        raise Exception("Invalid response from Readability")

    request.session['request_token'] = dict(cgi.parse_qsl(content))
    url = "%s?oauth_token=%s&oauth_callback=%s" % (AUTHORIZATION_URL, 
           request.session['request_token']['oauth_token'], CALLBACK_URL)

    return HttpResponseRedirect(url)

@login_required
def readability_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def readability_authenticated(request):
    token = oauth.Token(request.session['request_token']['oauth_token'],
            request.session['request_token']['oauth_token_secret'])
    token.set_verifier(request.GET['oauth_verifier'])

    client = oauth.Client(consumer, token)

    resp, content = client.request(ACCESS_TOKEN_URL, "GET")
    if resp['status'] != '200':
        raise Exception("Invalid response from Readability")

    access_token = dict(cgi.parse_qsl(content))
    token = oauth.Token(access_token['oauth_token'], 
            access_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    req = client.request(CURRENT_USER_URL, 'GET')
            
    req_json = json.loads(req[1])
    username = req_json['username']

    user = ''
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username,
            '%s@readability.com' % username,
            access_token['oauth_token_secret'])
        profile = UserProfile()
        profile.user = user
        profile.oauth_token = access_token['oauth_token']
        profile.oauth_secret = access_token['oauth_token_secret']
        profile.is_public = False
        profile.save()

    user = authenticate(username=user.get_profile().user,
        password=user.get_profile().oauth_secret)
   

    login(request, user)

    return HttpResponseRedirect("/profile/" + username) 

def fetch_bookmarks(username):
    u = User.objects.get(username__exact=username)
    user_profile = u.get_profile()
        
    token = oauth.Token(user_profile.oauth_token,
            user_profile.oauth_secret)
    client = oauth.Client(consumer, token)

    req = client.request(CURRENT_USER_URL, 'GET')
            
    req_json = json.loads(req[1])
    req = client.request(BOOKMARKS_URL + "?per_page=5&page=1", 'GET')
    
    meta = json.loads(req[1])['meta']
    bookmarks = json.loads(req[1])['bookmarks']

    user_profile.bookmarks = json.dumps(bookmarks)
    user_profile.save()

    return bookmarks

def profile(request, username):
    u = User.objects.get(username__exact=username)
    user_profile = u.get_profile()
    
    bookmarks = user_profile.bookmarks
    date_fetched = user_profile.date_fetched   

    parsed_data = {}
    if bookmarks == "":
        bookmarks = fetch_bookmarks(username)

    return render_to_response('profile.html', {'username': username, 
        'bookmarks': bookmarks}, 
        context_instance=RequestContext(request))
