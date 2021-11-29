#!/usr/bin/env python3
import tweepy
import random
from tweepy import StreamListener
from tweepy import Stream

from keys import *
from nlp import *
from emotions import *
from app import respond

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

me = 'b3rduck'

def clean_text(status):
    t = status.text
    try:
        for ent in status.entities['user_mentions']:
            print(ent['screen_name'])
            t = t.replace(ent['screen_name'],'')
            t = t.replace('@', '')
    except:
        print("no @mentions in text")
    return(t)

def get_reply(status):
    t = clean_text(status)
    stimulus = make_spacy_doc(t)
    mem = []
    try:
        qt = clean_text(status.quoted_status)
        mem.append(qt)
    except:
        print("quoted_status not available")
    try:
        rt = clean_text(api.get_status(status.in_reply_to_status_id))
        mem.append(rt)
    except:
        print("reply id not available")
    memory = make_spacy_doc(" ".join(mem))
    response = respond(stimulus, memory)
    return(response)

class StdOutListener(StreamListener):
    ''' Handles data received from the stream. '''

    def on_status(self, status):
        if 'RT' not in status.text:
            if status.author.screen_name != me:
                # Print the text of the tweet
                author = status.author.screen_name
                print('Tweet text:', status.text)
                print('Author:', author)


                if status.in_reply_to_user_id is not None:
                    if status.in_reply_to_screen_name == me:
                        print("Reply to post replying to me")
                        # Favorite the tweet
                        try:
                            api.create_favorite(status.id)
                        except:
                            print("favorite error")
                        try:
                            # api.retweet(status.id)
                            reply = get_reply(status)
                            message = f'@{author} {reply}'
                            print("Response text: " + message)
                            api.update_status(status=message, in_reply_to_status_id=status.id)
                        except Exception as e:
                                print('tweet error', e)
                    elif random.randint(1,50) == 50:
                        # Favorite the tweet
                        try:
                            api.create_favorite(status.id)
                        except:
                            print("favorite error")
                        # QT if talking to a stranger
                        if status.in_reply_to_screen_name != me and status.in_reply_to_user_id != status.author.id:
                        # Retweet posts sent to others, with comment
                            print("Quote")
                            try:
                                # api.retweet(status.id)
                                reply = get_reply(status)
                                # reply = "HELLO USER @" + s
                                url = f'https://twitter.com/{author}/status/{str(status.id)}'
                                message = f'{reply} {url}'
                                print("Response text: " + message)
                                api.update_status(status=message)
                            except Exception as e:
                                    print('tweet error', e)
                        if status.in_reply_to_user_id == status.author.id:
                        # Reply back to friends' selfposts
                            print("Reply to thread post")
                            try:
                                # api.retweet(status.id)
                                reply = get_reply(status)
                                message = f'@{author} {reply}'
                                print("Response text: " + message)
                                api.update_status(status=message, in_reply_to_status_id=status.id)
                            except Exception as e:
                                    print('tweet error', e)
                    else:
                        print("not replying to 49/50 replies")
                        # print("not replying to 19/20 replies")
                else:
                    # Reply back to users
                    print("Reply to top-level post")
                    if random.randint(1,20) >= 20:
                        # Favorite the tweet
                        try:
                            api.create_favorite(status.id)
                        except:
                            print("favorite error")
                        try:
                            # api.retweet(status.id)
                            reply = get_reply(status)
                            message = f'@{author} {reply}'
                            print("Response text: " + message)
                            api.update_status(status=message, in_reply_to_status_id=status.id)
                        except Exception as e:
                                print('tweet error', e)
                    else:
                        print("not replying to 19/20 tweets")
            print('-----------------------------')
        return True

    def on_error(self, status_code):
        if status_code == 420:
            return False
        else:
            print('Got an error with status code: ' + str(status_code))
            return True # To continue listening

    def on_timeout(self):
        print('Timeout...')
        return True # To continue listening

if __name__ == '__main__':
    print("Starting stream")
    listener = StdOutListener()

    stream = Stream(auth, listener)
    followers = [follower.id_str for follower in tweepy.Cursor(api.followers).items()]
    # Follow @IGRRpod aggressively because he asked for it
    # followers.append('1133920735984963584')
    stream.filter(follow=followers)
    # stream.filter(track=[me])
