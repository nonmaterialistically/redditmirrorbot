import telegram
import praw
import logging
import html
import sys
import json

from time import sleep
from datetime import datetime

#Set logging options
log = logging.getLogger('redditmirrorbot')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

#Open the settings file and get everything
settings = {}
with open('settings.json') as file:
    settings = json.load(file)

#Set sub to get posts from
sub = settings['reddit']['subreddit']

#Reddit and Telegram objects initializing with the credentials
r = praw.Reddit(user_agent="redditmirrorbot", client_id=settings['reddit']['client_id'], client_secret=settings['reddit']['client_secret'])
r.read_only = True
subreddit = r.subreddit(sub)
bot = telegram.Bot(token=settings['telegram']['token'])

#Start time
start_time = datetime.utcnow().timestamp()

def prev_submissions():
    try:
        with open('prev_submissions.id', 'r') as f:
            return f.read().splitlines()
    except:
        return None

def write_submissions(sub_id):
    try:
        with open('prev_submissions.id', 'a') as f:
            f.write('\n' + sub_id)
            f.close()
    except:
        log.expection("Error writing sub ID!")

last_sub_ids = prev_submissions()

if not last_sub_ids:
    #Create the submissions file if not present
    log.info("Latest submissions file not found, starting from scratch")
    with open('prev_submissions.id', 'w') as f:
        f.close()
else:
    log.info("Last posted submission is {}".format(last_sub_ids[-1]))

while True:
    try:
        #Get the top 5 hot submissions
        for submission in subreddit.hot(limit=10):
            try:
                #When we start from scratch, the prev_submissions.id file will be empty. Make sure we skip checking for past submissions and go directly to posting the first link
                if last_sub_ids is not None:
                    #Only post the link if it wasn't posted before
                    if submission.id in last_sub_ids:
                        log.info("Skipping {id} --- already posted!".format(id=submission.id))
                        continue
                #Get the needed fields and get the message ready
                permalink = "https://redd.it/{id}".format(id=submission.id)
                source = html.escape(submission.url or '')
                title = html.escape(submission.title or '')
                template = "{title} [<a href='{source}'>source</a>, <a href='{permalink}'>comments</a>]\n"
                message = template.format(title=title, source=source, permalink=permalink)

                #Log the post
                log.info("Posting {}".format(permalink))
                #bot.sendPhoto(chat_id=channel, photo=submission.url)
                bot.sendMessage(chat_id=settings['telegram']['channel_id'], parse_mode=telegram.ParseMode.HTML, text=message, disable_web_page_preview=True)

                write_submissions(submission.id)
            except Exception as e:
                log.exception("Error parsing {}".format(permalink))
        #Wait one hour before getting the submissions again
        sleep(3600)
        #Then update the submissions that are already posted
        last_sub_ids = prev_submissions()
    except Exception as e:
        log.exception("Error fetching new submissions, restarting in 10 secs")
        sleep(10)
