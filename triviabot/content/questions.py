import random
import time
from triviabot.utilities import strip_tags, separate_name

import triviabot.db as db


class Question:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer.lower()

        self.created = time.time()

    def solve_question(self, bot, user, channel, answer):
        """Called when someone answered correctly."""
        nick, identifier, hostname = separate_name(user)

        with db.session_scope() as session:
            user = db.get_user(session, nick)

            if not user:
                user = db.create_user(session, nick)

            db.update_score(session, nick, 15)  # TODO remove hardcoded score per question solved

            score = user.score

        bot.send_msg(channel, 'Correct answer "{answer}" by {nick}! Your new score is {score}.'
                     .format(answer=answer, nick=nick, score=score))

    def expire(self, bot, channel, event):
        """Called when the duration of question is over."""
        time.sleep(5.0)
        if not event.consumed:
            bot.del_event(event)
            bot.send_msg(channel, 'Time is up! The correct answer is "{answer}".'.format(answer=self.answer.title()))


# Utility functions
def get_random_champion_id(watcher):
    """Returns a random champion id."""
    champions = watcher.static_get_champion_list()['data']

    return champions[random.choice(champions.keys())]['id']


def get_random_item_id(watcher):
    """Returns a random item id."""
    items = watcher.static_get_item_list()['data']
    return items[random.choice(items.keys())]['id']


def get_random_summoner_spell_id(watcher):
    """Returns a random summoner spell id."""
    summoner_spells = watcher.static_get_summoner_spell_list()['data']
    return summoner_spells[random.choice(summoner_spells.keys())]['id']


def strip_champion_name(text, name):
    """Removes the champion name from texts such as lore."""
    return text.replace(name, '-----')

# Generators
# def example_generator(watcher):
#     # type: (None) -> Question
#     return random.choice([Question('Is this real life?', 'Is this just fantasy?'), Question('What\'s 1+1?', '2')])
#     return question


def generate_question(watcher):
    """Returns a Question from a randomly chosen generator."""
    return random.choice(_question_generators)(watcher)


# TODO Document generator functions
# TODO Make this code less repetitive
# Champion Data
def champion_from_spell_name(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='spells')

    name = str(champion['name'])
    spell = str(random.choice(champion['spells'])['name'])  # Choose a random spell

    return Question('Which champion has a skill called "{spell}"?'.format(spell=spell), name)


def spell_name_from_champion(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='spells')

    name = str(champion['name'])
    spell = random.choice(champion['spells'])  # Choose a random spell
    spell_name = str(spell['name'])
    spell_key = str(spell['key'][-1:])

    return Question('What\'s the name of {champion}\'s {spell}?'
                        .format(champion=name, spell=spell_key.upper()), spell_name)


def spell_name_from_description(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='spells')

    name = str(champion['name'])
    spell = random.choice(champion['spells'])  # Choose a random spell
    spell_name = str(spell['name'])
    spell_description = strip_champion_name(strip_champion_name(str(spell['sanitizedDescription']), name), spell_name)

    return Question('What\'s the name of the following spell? "{description}"'
                        .format(description=spell_description), spell_name)


def champion_from_title(watcher):  # TODO Add caching & Exception handling
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id)
    title = str(champion['title'])
    name = str(champion['name'])

    return Question('Which champion has the title "{title}"?'.format(title=title), name)


def champion_from_enemytips(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='enemytips,spells')
    name = str(champion['name'])
    tips = str(strip_champion_name(' '.join(champion['enemytips']), name))
    spells = champion['spells']

    for spell in spells:
        tips = strip_champion_name(tips, spell['name'])

    tips = str(tips)

    return Question('Which champion are you playing against if you should follow these tips? \n{tips}'
                        .format(tips=tips), name)


def champion_from_allytips(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='allytips,spells')
    name = str(champion['name'])
    tips = str(strip_champion_name(' '.join(champion['allytips']), name))

    spells = champion['spells']

    for spell in spells:
        tips = strip_champion_name(tips, spell['name'])

    tips = str(tips)

    return Question('Which champion do you have in your team if you should follow these tips? \n{tips}'
                        .format(tips=tips), name)


def champion_from_blurb(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='blurb')
    name = str(champion['name'])
    blurb = str(strip_champion_name(strip_tags(champion['blurb']), name))

    return Question('Which champion\'s lore is this? {blurb}'.format(blurb=blurb), name)


def champion_from_skins(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='skins')
    name = str(champion['name'])
    skins = champion['skins']

    skin_string = ''

    for skin in skins[1:]:  # [1:] to skip the default skin
        skin_string += str(skin['name']) + ', '

    skin_string = strip_champion_name(skin_string[:-2], name)  # remove trailing comma

    return Question('Which champion\'s skins are these? {skins}'.format(skins=skin_string), name)


def champion_from_passive(watcher):
    champion_id = get_random_champion_id(watcher)

    champion = watcher.static_get_champion(champion_id, champ_data='passive')
    name = str(champion['name'])
    passive = str(strip_champion_name(champion['passive']['sanitizedDescription'], name))

    return Question('Which champion\'s passive is this? {passive}'.format(passive=passive), name)


# Item Data
def item_from_description(watcher):
    item_id = get_random_item_id(watcher)

    item = watcher.static_get_item(item_id, item_data='sanitizedDescription')
    name = item['name']
    description = item['sanitizedDescription']

    return Question('Which item is this? {description}'.format(description=description), name)


def item_from_plaintext(watcher):
    item_id = get_random_item_id(watcher)

    item = watcher.static_get_item(item_id)
    name = item['name']
    plaintext = item['plaintext']

    return Question('Which item is this? {description}'.format(description=plaintext), name)


def item_gold_cost(watcher):
    item_id = get_random_item_id(watcher)

    item = watcher.static_get_item(item_id, item_data='gold')
    name = item['name']
    gold = str(item['gold']['total'])

    return Question('How much is {item}?'.format(item=name), gold)


def item_gold_sell(watcher):
    item_id = get_random_item_id(watcher)

    item = watcher.static_get_item(item_id, item_data='gold')
    name = item['name']
    gold = str(item['gold']['sell'])

    return Question('How much does {item} sell for?'.format(item=name), gold)


def item_stat(watcher):
    # FIXME make stat readable & answer non-float but also accept percentages
    item_id = get_random_item_id(watcher)

    item = watcher.static_get_item(item_id, item_data='stats')
    name = item['name']

    if item['stats']:
        stat = random.choice(item['stats'].keys())
        value = str(item['stats'][stat])

        return Question('How much {stat} does {item} give you?'.format(stat=stat, item=name), value)
    else:  # Some items don't have stats, e.g. Total Biscuit of Rejuvenation
        return generate_question(watcher)


# Summoner spells
def summoner_from_description(watcher):
    summoner_spell_id = get_random_summoner_spell_id(watcher)

    summoner_spell = watcher.static_get_summoner_spell(summoner_spell_id, spell_data='sanitizedDescription')
    name = summoner_spell['name']
    description = summoner_spell['sanitizedDescription']

    return Question('Which summoner spell is this? {text}'.format(text=description), name)


def summoner_cooldown(watcher):
    summoner_spell_id = get_random_summoner_spell_id(watcher)

    summoner_spell = watcher.static_get_summoner_spell(summoner_spell_id, spell_data='cooldownBurn')
    name = summoner_spell['name']
    cd = summoner_spell['cooldownBurn']

    return Question('What\'s the cooldown of "{spell}"? (without masteries)'.format(spell=name), cd)


_question_generators = [
    # Pretty name -> function callback
    # example_generator,
    spell_name_from_champion,
    spell_name_from_description,
    champion_from_title,
    champion_from_spell_name,
    champion_from_enemytips,
    champion_from_allytips,
    champion_from_blurb,
    champion_from_skins,
    champion_from_passive,
    item_from_description,
    item_from_plaintext,
    item_gold_cost,
    item_gold_sell,
    # item_stat,  # FIXME
    summoner_from_description,
    summoner_cooldown,
]
