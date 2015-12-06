#!/usr/bin/env python3
import sys
import random
import yaml
import argparse
import tweepy
from twython import Twython, TwythonError

def get_api():
    '''Twythonオブジェクトを作る'''
    secrets_filename = '.oauth_secrets.yaml'
    with open(secrets_filename) as f:
        secrets = yaml.load(f)
    if 'oauth_token' not in secrets:
        # authentication first step
        auth = tweepy.OAuthHandler(consumer_key=secrets['app_key'],
                                   consumer_secret=secrets['app_secret'])
        print(auth.get_authorization_url())
        pin = input('Enter PIN code: ')

        # final step
        oauth_token ,oauth_token_secret = auth.get_access_token(pin)
        secrets['oauth_token'], secrets['oauth_token_secret'] = oauth_token ,oauth_token_secret
        with open(secrets_filename, 'w') as f:
            yaml.dump(secrets, f)
    else:
        auth = tweepy.OAuthHandler(consumer_key=secrets['app_key'],
                                   consumer_secret=secrets['app_secret'])
        auth.set_access_token(secrets['oauth_token'], secrets['oauth_token_secret'])
    auth.get_username()         # set screen_name to auth.username
    api = tweepy.API(auth)
    return api

class StreamListener(tweepy.StreamListener):
    def __init__(self):
        self.latest_status = None
        self.latest_event = None

    def on_status(self, status):
        print('! status')
        self.latest_status = status
        print(self.latest_status)

        # when sent reply
        if '@' + api.auth.username in status.text:

            # unfollow if 'フォロー解除' in text
            if 'フォロー解除' in status.text:
                api.destroy_friendship(screen_name=status.author.screen_name)
                reply_tweet(status.author,screen_name, '今までありがとう♥ またね、ばいばい。')
                
            # refollow if 'フォロー' in text
            elif 'フォロー' in status.text:
                api.create_friendship(screen_name=status.author.screen_name)
                reply_tweet(status.author.screen_name, 'よろしくね♥')
        
    def on_event(self, event):
        print('! event')
        self.latest_event = event
        print(self.latest_event)

        screen_name = event.source.get('screen_name')
        
        # when followed
        if event.event == 'follow' and \
           event.target.get('screen_name') == api.auth.username:
            
            # if by protected user, refollow he/r
            if event.source.get('protected'):
                api.create_friendship(screen_name=screen_name)
                reply_tweet(screen_name, 'フォローしてくれてありがとうキュピコン♪ フォロー解除してほしい時は、ななみに 「フォロー解除」って言ってね♥')

            # otherwise, give information how to refollow
            else:
                reply_tweet(screen_name, 'フォローしてくれてありがとうキュピコン♪ ななみにフォローしてほしい時には、「フォロー」って言ってね♥ 「フォロー解除」って言うと、フォローを解除するよ。')

    def on_error(self, error_code):
        print('error:', error_code)

def reply_tweet(screen_name, status):
    status = '@{} {}'.format(screen_name, status)
    api.update_status(status=status)

def make_text_kyupikons():
    '''ななみがきゅぴこんするbot(@nanami_kyupikon) 由来の30種類+αの「きゅぴこん」を作成する'''
    firsts = ['きゅぴこん', 'きゅぴこ〜ん', 'きゅっぴこ〜ん',
              'キュピコン', 'キュピコ〜ン', 'キュッピコ〜ン']
    lasts = [''] + [mark * n for mark in ['♡', '♥', '！', '？', '♪', '♫', '★', '☆', '✨'] for n in range(1, 3)]
    kyupikons = [''.join((x, y)) for x in firsts for y in lasts]
    random.shuffle(kyupikons)
    return kyupikons


def tweet_kyupikon(action='random_choice'):
    if action == 'random_choice':
        status = get_text_kyupikon()
    print('--')
    print('Tweeting: \'{}\''.format(status))
    try:
        api.update_status(status=status)
    except TwythonError as e:
        print(e, file=sys.stderr)

def get_tweets_text_list():
    return [tw.text for tw in api.user_timeline(count=100)]

def get_text_kyupikon():
    global text_kyupikons_queue
    if not text_kyupikons_queue:
        text_kyupikons_queue = make_text_kyupikons()
    kyupikon = text_kyupikons_queue.pop()

    # update yaml
    with open('text_kyupikons_queue.yaml', 'w') as f:
        yaml.dump(text_kyupikons_queue, f, allow_unicode=True)
    
    return kyupikon
    
def load_text_kyupikons_queue():
    with open('text_kyupikons_queue.yaml') as f:
        queue = yaml.load(f)
    return queue

if __name__ == '__main__':
    text_kyupikons_queue = load_text_kyupikons_queue()
    api = get_api()

    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['tweet_kyupikon', 'stream'])
    args = parser.parse_args()

    if args.action == 'tweet_kyupikon':
        tweet_kyupikon()
    elif args.action == 'stream':
        stream_listener = StreamListener()
        stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
        stream.userstream(replies=all, track=['@nanami_kyupiko'])
