#!/usr/bin/env python3
import sys
import random
import yaml
import argparse
import tweepy

def get_api():
    '''TweepyのREST APIオブジェクトを作る'''
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
                tweet('今までありがとう♥ またね、ばいばい。', status.author.screen_name)
                
            # refollow if 'フォロー' in text
            elif 'フォロー' in status.text:
                api.create_friendship(screen_name=status.author.screen_name)
                tweet('よろしくね♥', status.author.screen_name)

            # otherwise, reply 'きゅぴこん♥' selected at random
            else:
                kyupikon = get_text_kyupikon_reply()
                tweet(kyupikon, status.author.screen_name)
        
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
                tweet('フォローしてくれてありがとうキュピコン♪ フォロー解除してほしい時は、ななみに「フォロー解除」って言ってね♥', screen_name)

            # otherwise, give information how to refollow
            else:
                tweet('フォローしてくれてありがとうキュピコン♪ ななみにフォローしてほしい時には、「フォロー」って言ってね♥ 「フォロー解除」って言うと、フォローを解除するよ。', screen_name)

    def on_error(self, error_code):
        print('error:', error_code)

def tweet(status, screen_name=None):
    '''statusで指定したテキストをツイートをする。screen_nameがあればリプライを送る'''
    if screen_name:
        status = '@{} {}'.format(screen_name, status)
    try:
        api.update_status(status=status)
        print('--')
        print('Tweeted: \'{}\''.format(status))
    except tweepy.TweepError as e:
        print(e, file=sys.stderr)

def make_text_kyupikons():
    '''ななみがきゅぴこんするbot(@nanami_kyupikon) 由来の30種類+αの「きゅぴこん」を作成する'''
    firsts = ['きゅぴこん', 'きゅぴこ〜ん', 'きゅっぴこ〜ん',
              'キュピコン', 'キュピコ〜ン', 'キュッピコ〜ン']
    lasts = [''] + [mark * n for mark in ['♡', '♥', '！', '？', '♪', '♫', '★', '☆', '✨'] for n in range(1, 3)]
    kyupikons = [''.join((x, y)) for x in firsts for y in lasts]
    random.shuffle(kyupikons)
    return kyupikons

def tweet_kyupikon():
    '''ランダムに選ばれた「きゅぴこん♥」のキューから一つ取り出してツイートする'''
    status = get_text_kyupikon()
    tweet(status)
        
def get_tweets_text_list():
    '''デバッグ用: 最新100個のツイートテキストのリストを取得する'''
    return [tw.text for tw in api.user_timeline(count=100)]

def get_text_kyupikon():
    '''「きゅぴこん♥」のキューから一つ取り出してテキストを返す'''
    global text_kyupikons_queue
    if not text_kyupikons_queue:
        text_kyupikons_queue = make_text_kyupikons()
    kyupikon = text_kyupikons_queue.pop()

    # update queue
    save_yaml('text_kyupikons_queue.yaml', text_kyupikons_queue)

    return kyupikon
    
def get_text_kyupikon_reply():
    '''リプライ用の「きゅぴこん♥」のキューから一つ取り出してテキストを返す'''
    global text_kyupikons_reply_queue
    if not text_kyupikons_reply_queue:
        text_kyupikons_reply_queue = make_text_kyupikons()
    kyupikon = text_kyupikons_reply_queue.pop()

    # update queue
    save_yaml('text_kyupikons_reply_queue.yaml', text_kyupikons_reply_queue)

    return kyupikon
    
def load_yaml(filename):
    with open(filename) as f:
        data = yaml.load(f)
    return data

def save_yaml(filename, data):
    with open(filename, 'w') as f:
        yaml.dump(data, f, allow_unicode=True)
    
if __name__ == '__main__':
    text_kyupikons_queue = load_yaml('text_kyupikons_queue.yaml')
    text_kyupikons_reply_queue = load_yaml('text_kyupikons_reply_queue.yaml')
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
