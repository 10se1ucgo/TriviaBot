import threading
import functools

from twisted.internet import reactor

import riotwatcher
from riotwatcher import RateLimit, EUROPE_WEST

from content.questions import generate_question
from config import config
from utilities import separate_name
from mod_help import add_helptext

watcher = None


def on_load(bot):
    bot.add_command('trivia', trivia)
    add_helptext('trivia', 'Stars a new round of trivia.')

    global watcher
    watcher = riotwatcher.RiotWatcher(config['api_key'], default_region=EUROPE_WEST,
                                      limits=(RateLimit(10, 10), RateLimit(500, 600), ))


def trivia(bot, user, channel, args):
    """Starts a new round of trivia."""
    nick, identifier, hostname = separate_name(user)

    # Notify the channel that someone started a new round
    bot.send_msg(channel, '%s has started a new trivia round! Get ready!' % nick)

    # Prepare the question
    question = generate_question(watcher)
    duration = 20.0  # in seconds

    event = bot.Event(question.answer, channel, question.solve_question)
    bot.add_event(event)

    # Wait 5s before showing the question
    t = threading.Timer(5.0, functools.partial(bot.send_msg, channel, question.question))
    t.start()

    # Solve the question if nobody has answered correctly
    t = threading.Timer(duration, functools.partial(question.expire, bot, channel, event))
    t.start()
