#!/usr/bin/env python3
import sys
import random
import datetime
from dateutil.parser import parse
import yaml
import argparse
import tweepy
from apscheduler.schedulers.blocking import BlockingScheduler

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

        auth.get_username()
        secrets['screen_name'] = auth.username
        
        with open(secrets_filename, 'w') as f:
            yaml.dump(secrets, f)
    else:
        auth = tweepy.OAuthHandler(consumer_key=secrets['app_key'],
                                   consumer_secret=secrets['app_secret'])
        auth.set_access_token(secrets['oauth_token'], secrets['oauth_token_secret'])
        auth.username = secrets.get('screen_name')
    api = tweepy.API(auth)
    return api

class StreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print('on_status')
        print_status(status)
        
        # not tweet by myself
        if status.author.screen_name != api.auth.username:
            
            # when sent reply by others
            if '@' + api.auth.username in status.text and \
               'RT' not in status.text:
                
                # unfollow if 'フォロー解除' in text
                if 'フォロー解除' in status.text:
                    api.destroy_friendship(screen_name=status.author.screen_name)
                    tweet('今までありがとう♥ またね、ばいばい。', status.author.screen_name, reply_id=status.id)
                    
                # refollow if 'フォロー' in text
                elif 'フォロー' in status.text:
                    api.create_friendship(screen_name=status.author.screen_name)
                    tweet('よろしくね♥', status.author.screen_name, reply_id=status.id)

                # add the user to deny list
                elif 'いいねしないで' in status.text:
                    deny_favorite_user_ids = load_yaml('deny_favorite_user_ids.yaml')
                    deny_favorite_user_ids.add(status.user.id)
                    save_yaml('deny_favorite_user_ids.yaml', deny_favorite_user_ids)
                    tweet('わかったきゅぴこん。ごめんね…(._.)', status.user.screen_name, reply_id=status.id)

                # remove the user from deny list
                elif 'いいねして' in status.text:
                    deny_favorite_user_ids = load_yaml('deny_favorite_user_ids.yaml')
                    if status.user.id in deny_favorite_user_ids:
                        deny_favorite_user_ids.remove(status.user.id)
                    save_yaml('deny_favorite_user_ids.yaml', deny_favorite_user_ids)
                    tweet('わかったきゅぴこん！', status.user.screen_name, reply_id=status.id)
                    
                # add the user to allow all kyupikon list
                elif 'ぜんぶきゅぴこんして' in status.text:
                    allow_all_kyupikon_user_ids = load_yaml('allow_all_kyupikon_user_ids.yaml')
                    allow_all_kyupikon_user_ids.add(status.user.id)
                    save_yaml('allow_all_kyupikon_user_ids.yaml', allow_all_kyupikon_user_ids)
                    tweet('きゅっぴこ〜ん♥♥♥', status.user.screen_name, reply_id=status.id)
                    
                # add the user to allow all kyupikon list
                elif 'ぜんぶきゅぴこんしないで' in status.text:
                    allow_all_kyupikon_user_ids = load_yaml('allow_all_kyupikon_user_ids.yaml')
                    if status.user.id in allow_all_kyupikon_user_ids:
                        allow_all_kyupikon_user_ids.remove(status.user.id)
                    save_yaml('allow_all_kyupikon_user_ids.yaml', allow_all_kyupikon_user_ids)
                    tweet('わかったきゅぴこん♪', status.user.screen_name, reply_id=status.id)
                    
                # otherwise, reply 'きゅぴこん♥' selected at random
                else:
                    kyupikon = get_text_kyupikon_reply()
                    tweet(kyupikon, status.author.screen_name, reply_id=status.id)

            # normal tweet by followers
            else:
                # reply 'きゅぴこん♥', if the user's id is in allow_all_kyupikon_user_ids
                allow_all_kyupikon_user_ids = load_yaml('allow_all_kyupikon_user_ids.yaml')
                if status.user.id in allow_all_kyupikon_user_ids:
                    kyupikon = get_text_kyupikon_reply()
                    tweet(kyupikon, status.author.screen_name, reply_id=status.id)

    def on_event(self, event):
        print('on_event')
        print_event(event)

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
                # when already following, e.g. followed at first from me
                if event.source.get('following'):
                    tweet('フォローしてくれてありがとうキュピコン♪ フォロー解除してほしい時は、ななみに「フォロー解除」って言ってね♥', screen_name)
                else:
                    tweet('フォローしてくれてありがとうキュピコン♪ ななみにフォローしてほしい時には、「フォロー」って言ってね♥ 「フォロー解除」って言うと、フォローを解除するよ。', screen_name)

    def on_error(self, error_code):
        print('error:', error_code, file=sys.stderr)

    def on_disconnect(self, notice):
        print('disconnect:', notice, file=sys.stderr)

    def on_warning(self, notice):
        print('warning:', notice, file=sys.stderr)

def tweet(status, screen_name=None, reply_id=None):
    '''statusで指定したテキストをツイートし、screen_nameがあればリプライを送る'''
    if screen_name:
        status = '@{} {}'.format(screen_name, status)
    try:
        if args.debug:
            print('Tweeting on debug: \'{}\''.format(status))
        else:
            api.update_status(status=status, in_reply_to_status_id=reply_id)
    except tweepy.TweepError as e:
        print('error on tweet():', e, file=sys.stderr)

def favorite(status):
    '''Statusオブジェクトとして指定されたツイートをfavoriteする'''
    favorited_ids = load_yaml('favorited_ids.yaml')
    deny_favorite_user_ids = load_yaml('deny_favorite_user_ids.yaml')
    if status.id not in favorited_ids and \
       status.user.id not in deny_favorite_user_ids:
        if not args.debug:
            print('Favoriting:')
            print_status(status)
            api.create_favorite(id=status.id)
            favorited_ids.add(status.id)
            save_yaml('favorited_ids.yaml', favorited_ids)
        else:
            print('Favorite on debug:')
            print_status(status)
        
def print_status(status, file=sys.stdout):
    '''Statusオブジェクトをリーダブルに表示する'''
    if isinstance(status, tweepy.Status):
        print('{} {}(@{}) {}'.format(status.created_at, status.user.name, status.user.screen_name, status.id), file=file)
        print(status.text, file=file)
    elif isinstance(status, dict):
        print('{} {}(@{}) {}'.format(parse(status['created_at']), status['user']['name'], status['user']['screen_name'], status['id']), file=file)
    else:
        print(status, file=file)
    print('-' * 20)

def print_event(event, file=sys.stdout):
    '''eventとしてのStatusオブジェクトをリーダブルに表示する'''
    print('event:', event.event, file=file)
    print('{}(@{}) -> {}(@{})'.format(event.source.get('name'), event.source.get('screen_name'),
                                      event.target.get('name'), event.target.get('screen_name'))
          , file=file)
    if 'target_object' in event.__dict__:
        print_status(event.target_object)
    else:
        print('-' * 20, file=file)

def print_rate_limit():
    '''APIのrate_limitを見やすく整形して表示する'''
    def print_element(key, element):
        if element.get('limit') == element.get('remaining'):
            mod = ' '
        else:
            mod = '*'
        print('{}\t{} {}\t{}\t{}'.format(element.get('limit'), element.get('remaining'), mod, str(datetime.datetime.fromtimestamp(element.get('reset'))), key))

    def print_rate_limit_iter(rate_limit, k=None):
        if 'limit' in rate_limit:
            print_element(k, rate_limit)
        elif isinstance(rate_limit, dict):
            for k,v in rate_limit.items():
                print_rate_limit_iter(v, k)

    print_rate_limit_iter(api.rate_limit_status())
                
def make_text_kyupikons():
    '''ななみがきゅぴこんするbot(@nanami_kyupikon) 由来の30種類+αの「きゅぴこん」を作成する'''
    firsts = ['きゅぴこん', 'きゅぴこ〜ん', 'きゅっぴこ〜ん',
              'キュピコン', 'キュピコ〜ン', 'キュッピコ〜ン']
    marks = ['♡', '♥', '！', '？', '♪', '☆', '✨', '🌟', '💕', '💞']
    postfixes = [mark * n for mark in marks for n in range(1, 3)]
    kyupikons = {first + postfix for first in firsts for postfix in postfixes}
    recents = {tw.text for tw in api.user_timeline(count=50)}
    inits = list(kyupikons & recents)
    lasts = list(kyupikons - recents)
    random.shuffle(inits)
    random.shuffle(lasts)
    kyupikons = inits + lasts
    return kyupikons

def tweet_kyupikon():
    '''ランダムに選ばれた「きゅぴこん♥」のキューから一つ取り出してツイートする'''
    status = get_text_kyupikon()
    tweet(status)

def favorite_kyupikon():
    '''「きゅぴこん|キュピコン」が含まれるツイートを検索してfavoriteする'''
    statuses = api.search(q='きゅぴこん OR キュピコン -RT -nanami_kyupiko', count=200)
    for status in statuses:
        favorite(status)

def process_stream():
    '''userstreamを読み込んで処理する'''
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    stream.userstream(replies=all, track=['@nanami_kyupiko -RT'])
    
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
    if not args.debug:
        with open(filename, 'w') as f:
            yaml.dump(data, f, allow_unicode=True)
    
if __name__ == '__main__':
    text_kyupikons_queue = load_yaml('text_kyupikons_queue.yaml')
    text_kyupikons_reply_queue = load_yaml('text_kyupikons_reply_queue.yaml')

    api = get_api()

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='enable debug mode to avoid actual tweeting')
    args = parser.parse_args()

    # set & run scheduler
    sched = BlockingScheduler()
    sched.add_job(process_stream)
    sched.add_job(tweet_kyupikon, 'cron', minute='*/15')
    sched.add_job(favorite_kyupikon, 'cron', minute='*')
    sched.start()
