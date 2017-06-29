#
# Copyright (c) 2017 by Rowdy Dog Software
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from .logging import get_logger
import collections
import random

class RandomInfiniteIterator():
    def __init__(self, items):
        self._items = list(items)
        self._refresh()
    def _refresh(self):
        random.shuffle(self._items)
        self._iter = iter(self._items)
    def next(self):
        rv = None
        tries = 2
        while tries > 0:
            tries -= 1
            try:
                rv = next(self._iter)
                tries = 0
            except StopIteration:
                self._refresh()
        return rv

class PrattlerBase():
    def __init__(self, tweeter, scheduler):
        super().__init__()
        self._logger = get_logger(__name__)
        self._tweeter = tweeter
        self._scheduler = scheduler
    def start(self):
        pass
    def stop(self):
        pass
    def get_next_prattle(self):
        return ['']
    def update_status(self, prattle):
        logger = self._logger
        for segment in prattle:
            logger.debug("segment = '{0}'".format(segment))
            broken = segment.split("\n")
            for line in broken:
                logger.debug("line    = '{0}'".format(line))
                self._tweeter.update_status(line)
    def _do_prattle(self):
        prattle = self.get_next_prattle()
        self.update_status(prattle)

class DoOncePrattler(PrattlerBase):
    def start(self, scheduler):
        self._do_prattle()

class RepeatingPrattler(PrattlerBase):
    def __init__(self, tweeter, scheduler):
        super().__init__(tweeter, scheduler)
        self._prattling_event = None
    def start(self):
        if self._prattling_event is None:
            self._schedule_next_prattle()
    def stop(self):
        if self._prattling_event is not None:
            try:
                self._scheduler.cancel(self._prattling_event)
                self._prattling_event = None
            except ValueError:
                pass
    def _schedule_next_prattle(self):
        next_delay = self.get_next_delay()
        self._prattling_event = self._scheduler.enter(next_delay, 999, self._time_for_prattle)
    def _time_for_prattle(self):
        self._do_prattle()
        self._schedule_next_prattle()
    def get_next_delay(self):
        return 24*60*60

class PrimeDelay1():
    def __init__(self):
        self._delay_minutes = RandomInfiniteIterator([23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67])
        self._delay_seconds = RandomInfiniteIterator([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59])
    def get_next_delay(self):
        minutes = self._delay_minutes.next()  # minutes = 0  #
        seconds = self._delay_seconds.next()
        return 60*minutes + seconds

class PrimeDelay2():
    def __init__(self):
        self._delay_seconds = RandomInfiniteIterator([23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67])
    def get_next_delay(self):
        seconds = self._delay_seconds.next()
        return seconds

class OctoPrintSuccessPrattler(DoOncePrattler):
    def __init__(self, tweeter, scheduler):
        super().__init__(tweeter, scheduler)
        self._phrase = RandomInfiniteIterator(
            [
                "Done! Another fine thing brought to you by your favourite Prattle Printer!",
                "Yippie yi yo kayah. I'm an old FDM and I come from Midlothian. I learned to heat, heat, heat 'fore I learned to print.\nOh. Sorry. I got bored.\nDone! What do you want to print next?"
                # http://www.elyrics.net/read/b/bing-crosby-lyrics/i_m-an-old-cowhand-lyrics.html
                # I'm an old cowhand and I come down from the Rio Grande
                # Yippie yi yo kayah.
                # I'm an old FDM and I come from Midlothian.
                # I learned to heat, heat, heat 'fore I learned to print.
            ])
    def get_next_prattle(self):
        phrase = self._phrase.next()
        return [phrase]

class OctoPrintInoperablePrattler(RepeatingPrattler):
    def __init__(self, tweeter, scheduler):
        super().__init__(tweeter, scheduler)
        self._phrase = RandomInfiniteIterator(
            [
                "Oh no! My hardware! I can't talk to my hardware! Something is terribly terribly wrong!",
                "Oh, lovely hardware. Why won't you talk to me? What have I done to deserve this scorn?",
                "Hardware not talking. Hardware not talking. Please help. Please help.",
                "Terrible day. Truly terrible day. I can't print. My hardware is ignoring me.",
                "My treacherous hardware has gone walkabout! If you find it, give it a righteous wholloping and send it home."
            ])
        self._delay = PrimeDelay1()
    def start(self):
        super().start()
        self._do_prattle()
    def get_next_prattle(self):
        phrase = self._phrase.next()
        return [phrase]
    def get_next_delay(self):
        return self._delay.get_next_delay()

class OctoPrintPausedPrattler(RepeatingPrattler):
    def __init__(self, tweeter, scheduler):
        super().__init__(tweeter, scheduler)
        self._phrase = RandomInfiniteIterator(
            [
                "Why oh why did you stop me! Printing is so much fun!",
                "Paused!!! Why? Why would you stop me?",
                "What pray tell would bring you to pause me?",
                "I was so close. Why would you pause me now?"
            ])
        self._delay = PrimeDelay2()
    def start(self):
        super().start()
        self._do_prattle()
    def get_next_prattle(self):
        phrase = self._phrase.next()
        return [phrase]
    def get_next_delay(self):
        return self._delay.get_next_delay()

PrattleColorInformation = collections.namedtuple('PrattleColorInformation',
        ['name', 'include_color_modifier_1', 'include_color_modifier_2'])

class OctoPrintIdlePrattler():
    _vowels = {'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U'}
    def __init__(self):
        self._size_modifier_1 = RandomInfiniteIterator(
            [
                'Big',
                'Colossal',
                'Compact',
                'Cosmic',
                'Elfin',
                'Enormous',
                'Epic',
                'Full-Size',
                'Gargantuan',
                'Giant',
                'Gigantic',
                'Ginormous',
                'Grand',
                'Great',
                'Huge',
                'Hulking',
                'Humongous',
                'Illimitable',
                'Immeasurable',
                'Immense',
                'Infinitesimal',
                'Large',
                'Life-Size',
                'Little',
                'Mammoth',
                'Massive',
                'Meager',
                'Measly',
                'Medium',
                'Microscopic',
                'Miniature',
                'Minuscule',
                'Oversize',
                'Petite',
                'Pint-Size',
                'Pocket-Size',
                'Puny',
                'Small',
                'Teensy',
                'Teeny',
                'Teeny-Tiny',
                'Teeny-Weeny',
                'Tiny',
                'Titanic',
                'Undersized',
                'Wee',
                'Whopping',
                None,
                None,
                None,
                None,
                None,
            ])
        self._color_modifier_1 = RandomInfiniteIterator(
            [
                'Translucent',
                'Opaque',
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None
            ])
        self._color_modifier_2 = RandomInfiniteIterator(
            [
                'Dark',
                'Light',
                'Deep',
                'Sparkly',
                'Vibrant',
                'Pale',
                None,
                None,
                None,
                None,
                None
            ])
        self._colors = RandomInfiniteIterator(
            [
                PrattleColorInformation('Glow-in-the-dark', False, False),
                PrattleColorInformation('Clear', False, False),
                # PrattleColorInformation('Alice-Blue', True, True),
                PrattleColorInformation('Antique-White', True, True),
                PrattleColorInformation('Aqua', True, True),
                PrattleColorInformation('Aquamarine', True, True),
                PrattleColorInformation('Azure', True, True),
                PrattleColorInformation('Beige', True, True),
                PrattleColorInformation('Bisque', True, True),
                PrattleColorInformation('Black', True, True),
                # PrattleColorInformation('Blanched-Almond', True, True),
                PrattleColorInformation('Blue', True, True),
                PrattleColorInformation('Blue-Violet', True, True),
                PrattleColorInformation('Brown', True, True),
                # PrattleColorInformation('Burlywood', True, True),
                PrattleColorInformation('Cadet-Blue', True, True),
                PrattleColorInformation('Chartreuse', True, True),
                PrattleColorInformation('Chocolate', True, True),
                PrattleColorInformation('Coral', True, True),
                PrattleColorInformation('Cornflower-Blue', True, True),
                # PrattleColorInformation('Cornsilk', True, True),
                PrattleColorInformation('Cyan', True, True),
                # PrattleColorInformation('Dodger-Blue', True, True),
                PrattleColorInformation('Firebrick', True, True),
                # PrattleColorInformation('Floral-White', True, True),
                PrattleColorInformation('Forest-Green', True, True),
                PrattleColorInformation('Fuchsia', True, True),
                # PrattleColorInformation('Gainsboro', True, True),
                PrattleColorInformation('Ghost-White', True, True),
                PrattleColorInformation('Gold', True, True),
                PrattleColorInformation('Goldenrod', True, True),
                # PrattleColorInformation('Goldenrod-Yellow', True, True),
                PrattleColorInformation('Gray', True, True),
                PrattleColorInformation('Green', True, True),
                PrattleColorInformation('Green-Yellow', True, True),
                PrattleColorInformation('Grey', True, True),
                # PrattleColorInformation('Honeydew', True, True),
                PrattleColorInformation('Hot-Pink', True, True),
                # PrattleColorInformation('Indian-Red', True, True),
                PrattleColorInformation('Ivory', True, True),
                PrattleColorInformation('Khaki', True, True),
                PrattleColorInformation('Lavender', True, True),
                # PrattleColorInformation('Lavender-Blush', True, True),
                PrattleColorInformation('Lawn-Green', True, True),
                PrattleColorInformation('Lemon-Chiffon', True, True),
                PrattleColorInformation('Lime', True, True),
                PrattleColorInformation('Lime-Green', True, True),
                # PrattleColorInformation('Linen', True, True),
                PrattleColorInformation('Magenta', True, True),
                PrattleColorInformation('Maroon', True, True),
                PrattleColorInformation('Midnight-Blue', True, True),
                # PrattleColorInformation('Mint-Cream', True, True),
                PrattleColorInformation('Misty-Rose', True, True),
                # PrattleColorInformation('Moccasin', True, True),
                # PrattleColorInformation('Navajo-White', True, True),
                PrattleColorInformation('Navy', True, True),
                PrattleColorInformation('Navy-Blue', True, True),
                # PrattleColorInformation('Old-Lace', True, True),
                PrattleColorInformation('Olive', True, True),
                # PrattleColorInformation('Olive-Drab', True, True),
                PrattleColorInformation('Olive-Green', True, True),
                PrattleColorInformation('Orange', True, True),
                PrattleColorInformation('Orange-Red', True, True),
                # PrattleColorInformation('Orchid', True, True),
                # PrattleColorInformation('Papaya-Whip', True, True),
                # PrattleColorInformation('Peach-Puff', True, True),
                # PrattleColorInformation('Peru', True, True),
                PrattleColorInformation('Pink', True, True),
                PrattleColorInformation('Plum', True, True),
                PrattleColorInformation('Powder-Blue', True, True),
                PrattleColorInformation('Purple', True, True),
                PrattleColorInformation('Rebecca-Purple', True, True),
                PrattleColorInformation('Red', True, True),
                # PrattleColorInformation('Rosy-Brown', True, True),
                PrattleColorInformation('Royal-Blue', True, True),
                PrattleColorInformation('Saddle-Brown', True, True),
                PrattleColorInformation('Salmon', True, True),
                # PrattleColorInformation('Sandy-Brown', True, True),
                PrattleColorInformation('Sea-Green', True, True),
                # PrattleColorInformation('Seashell', True, True),
                PrattleColorInformation('Sienna', True, True),
                PrattleColorInformation('Silver', True, True),
                PrattleColorInformation('Sky-Blue', True, True),
                PrattleColorInformation('Slate-Blue', True, True),
                PrattleColorInformation('Slate-Gray', True, True),
                PrattleColorInformation('Slate-Grey', True, True),
                # PrattleColorInformation('Snow', True, True),
                # PrattleColorInformation('Spring-Green', True, True),
                PrattleColorInformation('Steel-Blue', True, True),
                PrattleColorInformation('Tan', True, True),
                PrattleColorInformation('Teal', True, True),
                # PrattleColorInformation('Thistle', True, True),
                # PrattleColorInformation('Tomato', True, True),
                PrattleColorInformation('Turquoise', True, True),
                PrattleColorInformation('Violet', True, True),
                PrattleColorInformation('Violet-Red', True, True),
                # PrattleColorInformation('Wheat', True, True),
                PrattleColorInformation('White', True, True),
                # PrattleColorInformation('White-Smoke', True, True),
                PrattleColorInformation('Yellow', True, True),
                PrattleColorInformation('Yellow-Green', True, True),
            ])
        self._print_suggestion = RandomInfiniteIterator(
            [
                'Action Figure',
                'Angle Bracket',
                'Arm',
                'Base',
                'Batman',
                'Boat',
                'Box',
                'Brick',
                'Building',
                'Bushing',
                'Button',
                'Car',
                'Case',
                'Catapult',
                'Charger Holder',
                'Clamp',
                'Cleat',
                'Coin Sorter',
                'Condo',
                'Cover',
                'Dinosaur',
                'Doll',
                'Dome',
                'Dwarf',
                'Elf',
                'Excalibur',
                'Fan',
                'Fidget',
                'Finger',
                'Foot',
                'Forearm',
                'Frame',
                'Gauntlet',
                'Gear',
                'Gnome',
                'Groot',
                'Hand',
                'Head',
                'Holder',
                'Horn',
                'Infinity Stone',
                'iPhone Cover',
                'Joy-Con',
                # fix? Make this an optional modifier? 'Knurled',
                'Leg',
                'Lid',
                'Light House',
                'Malfoy Cane',
                'Measuring Stick',
                'Minion',
                'Mold',
                'Motor Housing',
                'Nut',
                'Part',
                'Pen',
                'Piano',
                'Plate',
                'Pokemon',
                'Pulley',
                'Ring',
                'Rollcage',
                'Roof',
                'Saber Guard',
                'Shaft',
                'Shuzo',
                'Skull',
                'Slide',
                'Spider',
                'Spider-Man',
                'Spinner',
                'Square',
                'Sword',
                'Thumb',
                'Vent',
                'Viking',
                'Violin',
                'Whistle',
            ])
        self._phrase = RandomInfiniteIterator(
            [
                "Anyone like {0} {1}?",
                "How 'bout {0} {1}?",
                "Aah, so you'd like {0} {1}.",
                "OK, here's my question: Would you like {0} {1}?",
                "Oh, very well. Here's my next question: Would you like {0} {1}?",
                "The next question is this: Given that God is infinite, and that the universe is also infinite... Would you like {0} {1}?",
                "I promise. This is my last question: If the entire universe is a finite state machine that stops running when maximum entropy is reached... Can I make {0} {1} for you?",
            ])
        self._delay_minutes = RandomInfiniteIterator([23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67])
        self._delay_seconds = RandomInfiniteIterator([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59])
    def get_next_prattle(self):
        size = self._size_modifier_1.next()
        color = self._colors.next()
        color_modifier_1 = self._color_modifier_1.next() if color.include_color_modifier_1 else None
        color_modifier_2 = self._color_modifier_2.next() if color.include_color_modifier_2 else None
        suggestion = self._print_suggestion.next()
        make_me = ' '.join(filter(lambda item: item is not None, (size, color_modifier_1, color_modifier_2, color.name, suggestion)))
        quantity = 'a'
        if len(make_me) > 0:
            if make_me[0] in OctoPrintIdlePrattler._vowels:
                quantity = 'an'
        phrase = self._phrase.next()
        prattle = phrase.format(quantity, make_me)
        broken = prattle.split('...')
        n1 = len(broken)-1
        for i1 in range(0, n1):
            broken[i1] = broken[i1].strip() + '...'
        broken[n1] = broken[n1].strip()
        return broken
    def get_next_delay(self):
        minutes = self._delay_minutes.next()  # minutes = 0  #
        seconds = self._delay_seconds.next()
        rv = 60*minutes + seconds
        return rv

class OctoPrintGetBusyPrattler():
    def __init__(self):
        self._phrase = RandomInfiniteIterator(
            [
                "Oh happy day! Squeezing hot plastic through my extruder is such a good feeling!"
            ])
    def get_next_prattle(self):
        phrase = self._phrase.next()
        return [phrase]


