"""
AnkiCraft add-on

Copyright: (c) Foxy_null 2023 <https://github.com/Foxy-null>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime, timedelta
from functools import lru_cache
import itertools
from os.path import join, dirname
import glob, random

from . import addons
from ._vendor import attr
from .config import local_conf

DEFAULT_GAME_ID = "halo_3"
all_game_ids = ["halo_3", "mw2", "halo_5", "halo_infinite", "vanguard", "trap_tower"]


class MultikillMixin:
    def requirements_met(
        self,
        question_shown_at,
        question_answered_at,
        interval_s,
        min_interval_s=0,
    ):
        delta = question_answered_at - question_shown_at
        return (
            timedelta(seconds=min_interval_s) <= delta < timedelta(seconds=interval_s)
        )


class KillingSpreeMixin:
    def requirements_met(
        self,
        question_shown_at,
        question_answered_at,
        interval_s,
        min_interval_s=0,
    ):
        delta = question_answered_at - question_shown_at
        return delta >= timedelta(seconds=min_interval_s)


# first just needs to be after minimum time
class MultikillStartingState(KillingSpreeMixin):
    is_displayable_medal = False
    is_earnable_medal = False
    rank = 0

    def next_streak_index(self, current_streak_index):
        return current_streak_index + 1


@attr.s(frozen=True)
class MultikillNoMedalState(MultikillMixin):
    is_displayable_medal = False
    is_earnable_medal = False
    rank = attr.ib(default=1)

    def next_streak_index(self, current_streak_index):
        return current_streak_index + 1


@attr.s(frozen=True)
class MultikillMedalState(MultikillMixin):

    id_ = attr.ib()
    name = attr.ib()
    name_jp = attr.ib()
    medal_image = attr.ib()
    medal_sound = attr.ib()
    rank = attr.ib()
    game_id = attr.ib()
    _call = attr.ib(default=None)
    is_earnable_medal = attr.ib(default=True)
    is_displayable_medal = attr.ib(default=True)

    if local_conf["language"] == "ja":

        @property
        def call(self):
            return self._call if self._call else self.name_jp

    else:

        @property
        def call(self):
            return self._call if self._call else self.name

    def next_streak_index(self, current_streak_index):
        return current_streak_index + 1


class EndState(MultikillMixin):
    def __init__(self, medal_state, index_to_return_to):
        self._medal_state = medal_state
        self._index_to_return_to = index_to_return_to

    def next_streak_index(self, _current_streak_index):
        return self._index_to_return_to

    def __getattr__(self, attr):
        return getattr(self._medal_state, attr)


class KillingSpreeNoMedalState(KillingSpreeMixin):
    is_displayable_medal = False
    is_earnable_medal = False

    def __init__(self, rank):
        self.rank = rank

    def next_streak_index(self, current_streak_index):
        return current_streak_index + 1


@attr.s(frozen=True)
class KillingSpreeMedalState(KillingSpreeMixin):
    id_ = attr.ib()
    name = attr.ib()
    name_jp = attr.ib()
    medal_image = attr.ib()
    medal_sound = attr.ib()
    rank = attr.ib()
    game_id = attr.ib()
    _call = attr.ib(default=None)
    is_displayable_medal = attr.ib(default=True)
    is_earnable_medal = attr.ib(default=True)

    if local_conf["language"] == "ja":

        @property
        def call(self):
            return self._call if self._call else self.name_jp

    else:

        @property
        def call(self):
            return self._call if self._call else self.name

    def next_streak_index(self, current_streak_index):
        return current_streak_index + 1


class InitialStreakState:
    def __init__(self, states, interval_s=8, current_streak_index=0):
        self.states = states
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index
        # If you switch games while reviewing, need to have a time to start with
        self._initialized_at = datetime.now()

    def on_show_question(self):
        return QuestionShownState(
            states=self.states,
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
            question_shown_at=datetime.now(),
        )

    # For case of switching games while reviewing
    def on_show_answer(self):
        return AnswerShownState(
            states=self.states,
            question_shown_at=self._initialized_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_answer(self, card_did_pass):
        answer_state = AnswerShownState(
            states=self.states,
            question_shown_at=self._initialized_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

        return answer_state.on_answer(card_did_pass)

    @property
    def current_medal_state(self):
        return self.states[self._current_streak_index]


def did_card_pass(answer, again_answer=1):
    return answer > again_answer


class Store:
    def __init__(self, state_machines):
        self.state_machines = state_machines

    def on_show_question(self):
        return self.__class__(
            state_machines=[m.on_show_question() for m in self.state_machines]
        )

    def on_show_answer(self):
        return self.__class__(
            state_machines=[m.on_show_answer() for m in self.state_machines]
        )

    def on_answer(self, card_did_pass):
        return self.__class__(
            state_machines=[
                m.on_answer(card_did_pass=card_did_pass) for m in self.state_machines
            ]
        )

    @property
    def current_earnable_medals(self):
        return [
            m.current_medal_state
            for m in self.state_machines
            if m.current_medal_state.is_earnable_medal
        ]

    @property
    def current_displayable_medals(self):
        return [
            m.current_medal_state
            for m in self.state_machines
            if m.current_medal_state.is_displayable_medal
        ]

    @property
    def all_displayable_medals(self):
        all_medals = itertools.chain.from_iterable(
            m.states for m in self.state_machines
        )

        return frozenset(medal for medal in all_medals if medal.is_displayable_medal)


class QuestionShownState:
    def __init__(
        self,
        states,
        question_shown_at,
        interval_s=8,
        current_streak_index=0,
        addon_is_installed_and_enabled=addons.is_installed_and_enabled,
    ):
        self.states = states
        self._question_shown_at = question_shown_at
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index
        self._addon_is_installed_and_enabled = addon_is_installed_and_enabled

    def on_show_question(self):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_show_answer(self):
        return AnswerShownState(
            states=self.states,
            question_shown_at=self._question_shown_at,
            answer_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_answer(self, card_did_pass):
        if self._addon_is_installed_and_enabled("Right Hand Reviews jkl"):
            answer_state = AnswerShownState(
                states=self.states,
                question_shown_at=self._question_shown_at,
                answer_shown_at=datetime.now(),
                interval_s=self._interval_s,
                current_streak_index=self._current_streak_index,
            )

            return answer_state.on_answer(card_did_pass)
        else:
            return self

    @property
    def current_medal_state(self):
        return self.states[self._current_streak_index]


class AnswerShownState:
    def __init__(
        self,
        states,
        question_shown_at,
        answer_shown_at,
        interval_s,
        current_streak_index,
    ):
        self.states = states
        self._question_shown_at = question_shown_at
        self._answer_shown_at = answer_shown_at
        self._interval_s = interval_s
        self._current_streak_index = current_streak_index

    def on_answer(self, card_did_pass):
        if self._advancement_requirements_met(card_did_pass, self._answer_shown_at):
            return self._advanced_state_machine()
        elif card_did_pass:
            # want this one to count for first kill in new streak
            return self._reset_state_machine(new_index=1)
        else:
            return self._reset_state_machine()

    def on_show_question(self):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self._current_streak_index,
        )

    def on_show_answer(self):
        """Can be triggered by edit field in review add-on"""
        return self

    def _advancement_requirements_met(self, card_did_pass, question_answered_at):
        requirements_for_current_state_met = self.current_medal_state.requirements_met(
            question_shown_at=self._question_shown_at,
            question_answered_at=question_answered_at,
            interval_s=self._interval_s,
        )

        return card_did_pass and requirements_for_current_state_met

    def _advanced_state_machine(self):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=self.current_medal_state.next_streak_index(
                self._current_streak_index
            ),
        )

    def _reset_state_machine(self, new_index=0):
        return QuestionShownState(
            states=self.states,
            question_shown_at=datetime.now(),
            interval_s=self._interval_s,
            current_streak_index=new_index,
        )

    @property
    def current_medal_state(self):
        return self.states[self._current_streak_index]


images_dir = join(dirname(__file__), "images")
sfx_dir = join(dirname(__file__), "sounds")


def image_path(filename):
    return join(images_dir, filename)


def sound_path(filename):
    random_sound = join(sfx_dir, filename)
    return random.choice(glob.glob(random_sound + "/*"))


@attr.s(frozen=True)
class NewAchievement:
    medal = attr.ib()
    deck_id = attr.ib()

    @property
    def medal_id(self):
        return self.medal.id_

    if local_conf["language"] == "ja":

        @property
        def medal_name(self):
            return self.medal.name_jp

    else:

        @property
        def medal_name(self):
            return self.medal.name

    @property
    def medal_img_src(self):
        return self.medal.medal_image

    @property
    def medal_sound_src(self):
        return self.medal.medal_sound


HALO_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="cave_killstreak_1",
            medal_image=image_path("halo_5/minecraft-bottle-o-enchanting.gif"),
            medal_sound=sound_path("orb"),
            name="Bottle o' Enchant ing",
            name_jp="エンチャントの瓶",
            game_id="halo_3",
            rank=3,
        ),
        index_to_return_to=1,
    ),
]

HALO_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(),
    MultikillMedalState(
        id_="乾燥した昆布",
        medal_image=image_path("Cobbled_Deepslate.webp"),
        medal_sound=sound_path("deepslate"),
        name="Cobbled Deepslate",
        name_jp="深層岩の丸石",
        game_id="halo_3",
        rank=2,
    ),
    MultikillMedalState(
        id_="石炭",
        medal_image=image_path("Coal.png"),
        medal_sound=sound_path("stone"),
        name="Coal",
        name_jp="石炭",
        game_id="halo_3",
        rank=3,
    ),
    MultikillMedalState(
        id_="鉄インゴット",
        medal_image=image_path("Iron_ingot.png"),
        medal_sound=sound_path("stone"),
        name="Iron Ingot",
        name_jp="鉄インゴット",
        game_id="halo_3",
        rank=4,
    ),
    MultikillMedalState(
        id_="レッドストーンダスト",
        medal_image=image_path("Redstone_Dust.png"),
        medal_sound=sound_path("stone"),
        name="Redstone Dust",
        name_jp="レッドストーンダスト",
        game_id="halo_3",
        rank=5,
    ),
    MultikillMedalState(
        id_="ラピスラズリ",
        medal_image=image_path("Lapis_Lazuli.png"),
        medal_sound=sound_path("stone"),
        name="Lapis Lazuli",
        name_jp="ラピスラズリ",
        game_id="halo_3",
        rank=6,
    ),
    MultikillMedalState(
        id_="ダイヤモンド",
        medal_image=image_path("Diamond.png"),
        medal_sound=sound_path("stone"),
        name="Diamond",
        name_jp="ダイヤモンド",
        game_id="halo_3",
        rank=7,
    ),
    MultikillNoMedalState(rank=8),
    MultikillNoMedalState(rank=9),
    EndState(
        medal_state=MultikillMedalState(
            id_="エメラルド",
            medal_image=image_path("Emerald.png"),
            medal_sound=sound_path("stone"),
            name="Emerald",
            name_jp="エメラルド",
            game_id="halo_3",
            rank=10,
        ),
        index_to_return_to=2,
    ),
]

HALO_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="丸石",
        medal_image=image_path("Cobblestone.png"),
        medal_sound=sound_path("stone"),
        name="Cobblestone",
        name_jp="丸石",
        game_id="halo_3",
        rank=1,
    ),
    KillingSpreeMedalState(
        id_="安山岩",
        medal_image=image_path("Andesite.webp"),
        medal_sound=sound_path("stone"),
        name="Andesite",
        name_jp="安山岩",
        game_id="halo_3",
        rank=2,
    ),
    KillingSpreeMedalState(
        id_="閃緑岩",
        medal_image=image_path("Diorite.webp"),
        medal_sound=sound_path("stone"),
        name="Diorite",
        name_jp="閃緑岩",
        game_id="halo_3",
        rank=3,
    ),
    KillingSpreeMedalState(
        id_="花崗岩",
        medal_image=image_path("Granite.webp"),
        medal_sound=sound_path("stone"),
        name="Granite",
        name_jp="花崗岩",
        game_id="halo_3",
        rank=4,
    ),
    KillingSpreeMedalState(
        id_="矢",
        medal_image=image_path("Arrow.png"),
        medal_sound=sound_path("bow"),
        name="Arrow",
        name_jp="矢",
        game_id="halo_3",
        rank=5,
    ),
    KillingSpreeMedalState(
        id_="銅インゴット",
        medal_image=image_path("Copper_Ingot.png"),
        medal_sound=sound_path("stone"),
        name="Copper Ingot",
        name_jp="金インゴット",
        game_id="halo_3",
        rank=6,
    ),
    KillingSpreeMedalState(
        id_="金インゴット",
        medal_image=image_path("Gold_Ingot.png"),
        medal_sound=sound_path("stone"),
        name="Gold Ingot",
        name_jp="金インゴット",
        game_id="halo_3",
        rank=7,
    ),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="金のリンゴ",
        medal_image=image_path("Golden_Apple.png"),
        medal_sound=sound_path("food"),
        name="Golden Apple",
        name_jp="金のリンゴ",
        game_id="halo_3",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeNoMedalState(rank=15),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeMedalState(
        id_="治癒のポーションII",
        medal_image=image_path("Splash_Potion_of_Healing.png"),
        medal_sound=sound_path("glass"),
        name="Splash Potion of Healing II",
        name_jp="治癒のポーションII",
        game_id="halo_3",
        rank=20,
    ),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeNoMedalState(rank=25),
    KillingSpreeNoMedalState(rank=26),
    KillingSpreeNoMedalState(rank=27),
    KillingSpreeNoMedalState(rank=28),
    KillingSpreeNoMedalState(rank=29),
    KillingSpreeNoMedalState(rank=30),
    KillingSpreeNoMedalState(rank=31),
    KillingSpreeNoMedalState(rank=32),
    KillingSpreeNoMedalState(rank=33),
    KillingSpreeNoMedalState(rank=34),
    KillingSpreeNoMedalState(rank=35),
    KillingSpreeNoMedalState(rank=36),
    KillingSpreeNoMedalState(rank=37),
    KillingSpreeNoMedalState(rank=38),
    KillingSpreeNoMedalState(rank=39),
    KillingSpreeNoMedalState(rank=40),
    KillingSpreeNoMedalState(rank=41),
    KillingSpreeNoMedalState(rank=42),
    KillingSpreeNoMedalState(rank=43),
    KillingSpreeNoMedalState(rank=44),
    KillingSpreeNoMedalState(rank=45),
    KillingSpreeNoMedalState(rank=46),
    KillingSpreeNoMedalState(rank=47),
    KillingSpreeNoMedalState(rank=48),
    KillingSpreeNoMedalState(rank=49),
    KillingSpreeMedalState(
        id_="エンチャントされた金のリンゴ",
        medal_image=image_path("Enchanted_Golden_Apple.gif"),
        medal_sound=sound_path("food"),
        name="Enchanted Golden Apple",
        name_jp="エンチャントされた金のリンゴ",
        game_id="halo_3",
        rank=50,
    ),
    KillingSpreeNoMedalState(rank=51),
    KillingSpreeNoMedalState(rank=52),
    KillingSpreeNoMedalState(rank=53),
    KillingSpreeNoMedalState(rank=54),
    KillingSpreeNoMedalState(rank=55),
    KillingSpreeNoMedalState(rank=56),
    KillingSpreeNoMedalState(rank=57),
    KillingSpreeNoMedalState(rank=58),
    KillingSpreeNoMedalState(rank=59),
    KillingSpreeNoMedalState(rank=60),
    KillingSpreeNoMedalState(rank=61),
    KillingSpreeNoMedalState(rank=62),
    KillingSpreeNoMedalState(rank=63),
    KillingSpreeNoMedalState(rank=64),
    KillingSpreeNoMedalState(rank=65),
    KillingSpreeNoMedalState(rank=66),
    KillingSpreeNoMedalState(rank=67),
    KillingSpreeNoMedalState(rank=68),
    KillingSpreeNoMedalState(rank=69),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="ネザライトインゴット",
            medal_image=image_path("Netherite_Ingot.webp"),
            medal_sound=sound_path("smithing_table"),
            name="Netherite Ingot",
            name_jp="ネザライトインゴット",
            game_id="halo_3",
            rank=70,
        ),
        index_to_return_to=1,
    ),
]

MW2_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="乾燥した昆布-1",
        medal_image=image_path("Dried_Kelp.webp"),
        medal_sound=sound_path("grass"),
        name="Dried Kelp",
        name_jp="乾燥した昆布",
        game_id="mw2",
        rank=1,
    ),
    KillingSpreeMedalState(
        id_="イカスミ",
        medal_image=image_path("mw2/Ink_Sac.webp"),
        medal_sound=sound_path("item"),
        name="Ink Sac",
        name_jp="イカスミ",
        game_id="mw2",
        # call="UAV recon standing by",
        rank=2,
    ),
    KillingSpreeMedalState(
        id_="砂岩",
        medal_image=image_path("mw2/Sandstone.png"),
        medal_sound=sound_path("stone"),
        name="Sandstone",
        name_jp="砂岩",
        game_id="mw2",
        # call="UAV recon standing by",
        rank=3,
    ),
    KillingSpreeMedalState(
        id_="粘土",
        medal_image=image_path("mw2/Clay_ball.png"),
        medal_sound=sound_path("gravel"),
        name="Clay Ball",
        name_jp="粘土",
        game_id="mw2",
        # call="Care package waiting for your mark",
        rank=4,
    ),
    KillingSpreeMedalState(
        id_="焼き鱈",
        medal_image=image_path("mw2/Cooked_Cod.png"),
        medal_sound=sound_path("fish"),
        name="Cooked Cod",
        name_jp="焼き鱈",
        game_id="mw2",
        # call="Predator missile ready for launch",
        rank=5,
    ),
    KillingSpreeMedalState(
        id_="焼き鮭",
        medal_image=image_path("mw2/Cooked_Salmon.png"),
        medal_sound=sound_path("fish"),
        name="Cooked Salmon",
        name_jp="焼き鮭",
        game_id="mw2",
        # call="Airstrike standing by",
        rank=6,
    ),
    KillingSpreeMedalState(
        id_="ガラスブロック",
        medal_image=image_path("mw2/Glass.png"),
        medal_sound=sound_path("glass"),
        name="Glass",
        name_jp="ガラスブロック",
        game_id="mw2",
        # call="Harrier's waiting for your mark",
        rank=7,
    ),
    KillingSpreeMedalState(
        id_="プリズマリンの欠片",
        medal_image=image_path("mw2/Prismarine_Shard.png"),
        medal_sound=sound_path("stone"),
        name="Prismarine Shard",
        name_jp="プリズマリンの欠片",
        game_id="mw2",
        # call="プリズマリンブロックをクラフト可能",
        rank=8,
    ),
    KillingSpreeMedalState(
        id_="プリズマリンクリスタル",
        medal_image=image_path("mw2/Prismarine_Crystals.png"),
        medal_sound=sound_path("glass"),
        name="Prismarine Crystals",
        name_jp="プリズマリンクリスタル",
        game_id="mw2",
        # call="シーランタンをクラフト可能",
        rank=9,
    ),
    KillingSpreeMedalState(
        id_="TNTブロック",
        medal_image=image_path("mw2/TNT.png"),
        medal_sound=sound_path("grass"),
        name="TNT",
        name_jp="TNTブロック",
        game_id="mw2",
        rank=10,
    ),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="輝くイカスミ",
            medal_image=image_path("mw2/Glow_Ink_Sac.webp"),
            medal_sound=sound_path("item"),
            name="Glow Ink Sac",
            name_jp="輝くイカスミ",
            game_id="mw2",
            rank=11,
        ),
        index_to_return_to=1,
    ),
]

MW2_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="砂",
        medal_image=image_path("mw2/Sand.png"),
        medal_sound=sound_path("sand"),
        name="Sand",
        name_jp="砂",
        game_id="mw2",
        rank=1,
    ),
    KillingSpreeMedalState(
        id_="砂利",
        medal_image=image_path("mw2/Gravel.webp"),
        medal_sound=sound_path("gravel"),
        name="Gravel",
        name_jp="砂利",
        game_id="mw2",
        rank=2,
    ),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="サトウキビ",
            medal_image=image_path("mw2/Suger_Cane.png"),
            medal_sound=sound_path("grass"),
            name="Suger Cane",
            name_jp="サトウキビ",
            game_id="mw2",
            rank=3,
        ),
        index_to_return_to=1,
    ),
]

HALO_5_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(),
    MultikillMedalState(
        id_="松明",
        medal_image=image_path("halo_5/Torch.png"),
        medal_sound=sound_path("wood"),
        name="Torch",
        name_jp="松明",
        game_id="halo_5",
        rank=2,
    ),
    MultikillMedalState(
        id_="オークの木材",
        medal_image=image_path("halo_5/Planks.png"),
        medal_sound=sound_path("wood"),
        name="Oak Planks",
        name_jp="オークの木材",
        game_id="halo_5",
        rank=3,
    ),
    MultikillMedalState(
        id_="オークの原木",
        medal_image=image_path("halo_5/Oak_Log.png"),
        medal_sound=sound_path("wood"),
        name="Oak Log",
        name_jp="オークの原木",
        game_id="halo_5",
        rank=4,
    ),
    MultikillMedalState(
        id_="白樺の原木",
        medal_image=image_path("halo_5/Birch_Log.png"),
        medal_sound=sound_path("wood"),
        name="Birch Log",
        name_jp="白樺の原木",
        game_id="halo_5",
        rank=5,
    ),
    MultikillMedalState(
        id_="ベイクドポテト",
        medal_image=image_path("halo_5/Baked_Potato.png"),
        medal_sound=sound_path("food"),
        name="Baked Potato",
        name_jp="ベイクドポテト",
        game_id="halo_5",
        rank=6,
    ),
    MultikillMedalState(
        id_="ステーキ",
        medal_image=image_path("halo_5/SteakNew.png"),
        medal_sound=sound_path("food"),
        name="Steak",
        name_jp="ステーキ",
        game_id="halo_5",
        rank=7,
    ),
    MultikillMedalState(
        id_="エンダーパール",
        medal_image=image_path("halo_5/Ender_Pearl.png"),
        medal_sound=sound_path("throw"),
        name="Ender Pearl",
        name_jp="エンダーパール",
        game_id="halo_5",
        rank=8,
    ),
    MultikillMedalState(
        id_="ロケット花火",
        medal_image=image_path("halo_5/Firework_Rocket.png"),
        medal_sound=sound_path("firework"),
        name="Firework rocket",
        name_jp="ロケット花火",
        game_id="halo_5",
        rank=9,
    ),
    EndState(
        medal_state=MultikillMedalState(
            id_="金のリンゴ-1",
            medal_image=image_path("Golden_Apple.png"),
            medal_sound=sound_path("food"),
            name="Golden Apple",
            name_jp="金のリンゴ",
            game_id="halo_5",
            rank=10,
        ),
        index_to_return_to=2,
    ),
]

HALO_5_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="土",
        medal_image=image_path("halo_5/Dirt.png"),
        medal_sound=sound_path("dirt"),
        name="Dirt",
        name_jp="土",
        game_id="halo_5",
        rank=1,
    ),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="矢-1",
        medal_image=image_path("Arrow.png"),
        medal_sound=sound_path("bow"),
        name="Arrow",
        name_jp="矢",
        game_id="halo_5",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeMedalState(
        id_="革",
        medal_image=image_path("halo_5/Leather.webp"),
        medal_sound=sound_path("item"),
        name="Leather",
        name_jp="革",
        game_id="halo_5",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="エンチャントの瓶",
        medal_image=image_path("halo_5/minecraft-bottle-o-enchanting.gif"),
        medal_sound=sound_path("orb"),
        name="Bottle o' Enchanting",
        name_jp="エンチャントの瓶",
        game_id="halo_5",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="鉄インゴット-1",
        medal_image=image_path("Iron_ingot.png"),
        medal_sound=sound_path("stone"),
        name="Iron Ingot",
        name_jp="鉄インゴット",
        game_id="halo_5",
        rank=15,
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeNoMedalState(rank=20),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeNoMedalState(rank=25),
    KillingSpreeNoMedalState(rank=26),
    KillingSpreeNoMedalState(rank=27),
    KillingSpreeNoMedalState(rank=28),
    KillingSpreeNoMedalState(rank=29),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="不死のトーテム",
            medal_image=image_path("halo_5/Totem_of_Undying.png"),
            medal_sound=sound_path("item"),
            name="Totem of Undying",
            name_jp="不死のトーテム",
            game_id="halo_5",
            rank=30,
        ),
        index_to_return_to=1,
    ),
]


HALO_INFINITE_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(),
    MultikillMedalState(
        id_="スイカの薄切り",
        medal_image=image_path("halo_infinite/melon-slice.png"),
        medal_sound=sound_path("food"),
        name="Melon Slice",
        name_jp="スイカの薄切り",
        game_id="halo_infinite",
        rank=2,
    ),
    MultikillMedalState(
        id_="リンゴ",
        medal_image=image_path("halo_infinite/apple.png"),
        medal_sound=sound_path("food"),
        name="Apple",
        name_jp="リンゴ",
        game_id="halo_infinite",
        rank=3,
    ),
    MultikillMedalState(
        id_="ニンジン",
        medal_image=image_path("halo_infinite/carrot.png"),
        medal_sound=sound_path("food"),
        name="Carrot",
        name_jp="ニンジン",
        game_id="halo_infinite",
        rank=4,
    ),
    MultikillMedalState(
        id_="パン",
        medal_image=image_path("halo_infinite/bread.png"),
        medal_sound=sound_path("food"),
        name="Bread",
        name_jp="パン",
        game_id="halo_infinite",
        rank=5,
    ),
    MultikillMedalState(
        id_="クッキー",
        medal_image=image_path("halo_infinite/cookie.png"),
        medal_sound=sound_path("food"),
        name="Cookie",
        name_jp="クッキー",
        game_id="halo_infinite",
        rank=6,
    ),
    MultikillMedalState(
        id_="パンプキンパイ",
        medal_image=image_path("halo_infinite/pumpkin_pie.png"),
        medal_sound=sound_path("food"),
        name="Pumpkin Pie",
        name_jp="パンプキンパイ",
        game_id="halo_infinite",
        rank=7,
    ),
    MultikillMedalState(
        id_="グロウベリー",
        medal_image=image_path("halo_infinite/glow_berries.png"),
        medal_sound=sound_path("cavevines"),
        name="Glow Berries",
        name_jp="グロウベリー",
        game_id="halo_infinite",
        rank=8,
    ),
    EndState(
        medal_state=MultikillMedalState(
            id_="ハチミツ入りの瓶",
            medal_image=image_path("halo_infinite/Honey_Bottle.png"),
            medal_sound=sound_path("honeybottle"),
            name="Honey Bottle",
            name_jp="ハチミツ入りの瓶",
            game_id="halo_infinite",
            rank=9,
        ),
        index_to_return_to=2,
    ),
]


HALO_INFINITE_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="スイートベリー",
        medal_image=image_path("halo_infinite/sweet-berries.png"),
        medal_sound=sound_path("berrybush"),
        name="Sweet Berries",
        name_jp="スイートベリー",
        game_id="halo_infinite",
        rank=1,
    ),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="焼き鳥",
        medal_image=image_path("halo_infinite/Cooked_Chicken.png"),
        medal_sound=sound_path("food"),
        name="Cooked Chicken",
        name_jp="焼き鳥",
        game_id="halo_infinite",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="焼き豚",
        medal_image=image_path("halo_infinite/Cooked_Porkchop.png"),
        medal_sound=sound_path("food"),
        name="Cooked Porkchop",
        name_jp="焼き豚",
        game_id="halo_infinite",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="金のリンゴ-2",
        medal_image=image_path("Golden_Apple.png"),
        medal_sound=sound_path("food"),
        name="Golden Apple",
        name_jp="金のリンゴ",
        game_id="halo_infinite",
        rank=15,
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="エンチャントされた金のリンゴ-1",
            medal_image=image_path("Enchanted_Golden_Apple.gif"),
            medal_sound=sound_path("food"),
            name="Enchanted Golden Apple",
            name_jp="エンチャントされた金のリンゴ",
            game_id="halo_infinite",
            rank=20,
        ),
        index_to_return_to=11,
    ),
]


VANGUARD_MULTIKILL_STATES = [
    MultikillStartingState(),
    EndState(
        medal_state=MultikillMedalState(
            id_="オークの原木-1",
            medal_image=image_path("halo_5/Oak_Log.png"),
            medal_sound=sound_path("wood"),
            name="Oak Log",
            name_jp="オークの原木",
            game_id="vanguard",
            rank=1,
        ),
        index_to_return_to=1,
    ),
]


VANGUARD_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="白樺の原木-1",
        medal_image=image_path("vanguard/Birch_Log.png"),
        medal_sound=sound_path("wood"),
        name="Birch Log",
        name_jp="白樺の原木",
        game_id="vanguard",
        rank=1,
    ),
    KillingSpreeMedalState(
        id_="トウヒの原木",
        medal_image=image_path("vanguard/Spruce_Log.png"),
        medal_sound=sound_path("wood"),
        name="Spruce Log",
        name_jp="トウヒの原木",
        game_id="vanguard",
        rank=2,
    ),
    KillingSpreeMedalState(
        id_="ダークオークの原木",
        medal_image=image_path("vanguard/Dark_Oak_Log.png"),
        medal_sound=sound_path("wood"),
        name="Dark Oak Log",
        name_jp="ダークオークの原木",
        game_id="vanguard",
        rank=3,
    ),
    KillingSpreeMedalState(
        id_="ジャングルの原木",
        medal_image=image_path("vanguard/Jungle_Log.png"),
        medal_sound=sound_path("wood"),
        name="Jungle Log",
        name_jp="ジャングルの原木",
        game_id="vanguard",
        rank=4,
    ),
    KillingSpreeMedalState(
        id_="アカシアの原木",
        medal_image=image_path("vanguard/Acacia_Log.png"),
        medal_sound=sound_path("wood"),
        name="Acacia Log",
        name_jp="アカシアの原木",
        game_id="vanguard",
        rank=5,
    ),
    KillingSpreeMedalState(
        id_="マングローブの原木",
        medal_image=image_path("vanguard/Mangrove_Log.png"),
        medal_sound=sound_path("wood"),
        name="Mangrove Log",
        name_jp="マングローブの原木",
        game_id="vanguard",
        rank=6,
    ),
    KillingSpreeMedalState(
        id_="サクラの原木",
        medal_image=image_path("vanguard/Cherry_Log.png"),
        medal_sound=sound_path("wood"),
        name="Cherry Log",
        name_jp="サクラの原木",
        game_id="vanguard",
        rank=7,
    ),
    KillingSpreeMedalState(
        id_="リンゴ-1",
        medal_image=image_path("halo_infinite/apple.png"),
        medal_sound=sound_path("food"),
        name="Apple",
        name_jp="リンゴ",
        game_id="vanguard",
        rank=8,
    ),
    KillingSpreeMedalState(
        id_="歪んだ原木",
        medal_image=image_path("vanguard/Warped_Stem.png"),
        medal_sound=sound_path("wood"),
        name="Warped Stem",
        name_jp="歪んだ原木",
        game_id="vanguard",
        rank=9,
    ),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="真紅の原木",
            medal_image=image_path("vanguard/Crimson_Stem.png"),
            medal_sound=sound_path("wood"),
            name="Crimson Stem",
            name_jp="真紅の原木",
            game_id="vanguard",
            rank=10,
        ),
        index_to_return_to=1,
    ),
]


VANGUARD_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeMedalState(
        id_="茶色のキノコ",
        medal_image=image_path("vanguard/BrownMushroomNew.png"),
        medal_sound=sound_path("grass"),
        name="Brown Mushroom",
        name_jp="茶色のキノコ",
        game_id="vanguard",
        rank=3,
    ),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="赤色のキノコ",
            medal_image=image_path("vanguard/RedMushroomNew.png"),
            medal_sound=sound_path("grass"),
            name="Red Mushroom",
            name_jp="赤色のキノコ",
            game_id="vanguard",
            rank=4,
        ),
        index_to_return_to=1,
    ),
]


trap_tower_layer1 = [
    MultikillStartingState(),
    MultikillMedalState(
        id_="trap_tower_layer1_1",
        medal_image=image_path("trap_tower/Rotten_Flesh.webp"),
        medal_sound=sound_path("zombie"),
        name="Rotten Flesh",
        name_jp="腐った肉",
        game_id="trap_tower",
        rank=1,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_2",
        medal_image=image_path("Arrow.png"),
        medal_sound=sound_path("item"),
        name="Arrow",
        name_jp="矢",
        game_id="trap_tower",
        rank=2,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_3",
        medal_image=image_path("trap_tower/Bone.webp"),
        medal_sound=sound_path("skeleton"),
        name="Bone",
        name_jp="骨",
        game_id="trap_tower",
        rank=3,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_4",
        medal_image=image_path("trap_tower/String.webp"),
        medal_sound=sound_path("spider"),
        name="String",
        name_jp="糸",
        game_id="trap_tower",
        rank=4,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_5",
        medal_image=image_path("trap_tower/Spider_Eye.webp"),
        medal_sound=sound_path("spider"),
        name="Spider Eye",
        name_jp="クモの目",
        game_id="trap_tower",
        rank=5,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_6",
        medal_image=image_path("trap_tower/Slimeball.webp"),
        medal_sound=sound_path("slime"),
        name="Slimeball",
        name_jp="スライムボール",
        game_id="trap_tower",
        rank=6,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_7",
        medal_image=image_path("trap_tower/Gold_Nugget.webp"),
        medal_sound=sound_path("item"),
        name="Gold Nugget",
        name_jp="金塊",
        game_id="trap_tower",
        rank=7,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_8",
        medal_image=image_path("trap_tower/Magma_Cream.webp"),
        medal_sound=sound_path("slime"),
        name="Magma Cream",
        name_jp="マグマクリーム",
        game_id="trap_tower",
        rank=8,
    ),
    MultikillMedalState(
        id_="trap_tower_layer1_9",
        medal_image=image_path("trap_tower/Blaze_Rod.webp"),
        medal_sound=sound_path("blaze"),
        name="Blaze Rod",
        name_jp="ブレイズロッド",
        game_id="trap_tower",
        rank=9,
    ),
    EndState(
        MultikillMedalState(
            id_="trap_tower_layer1_10",
            medal_image=image_path("Emerald.png"),
            medal_sound=sound_path("item"),
            name="Emerald",
            name_jp="エメラルド",
            game_id="trap_tower",
            rank=10,
        ),
        index_to_return_to=1,
    ),
]


# trap_tower_layer_2 = [
#     KillingSpreeNoMedalState(rank=0),
#     KillingSpreeNoMedalState(rank=1),
#     KillingSpreeNoMedalState(rank=2),
#     KillingSpreeNoMedalState(rank=3),
#     KillingSpreeNoMedalState(rank=4),
#     KillingSpreeMedalState(
#         id_="trap_tower_layer3_0",
#         medal_image=image_path("halo_5/minecraft-bottle-o-enchanting.gif"),
#         name="エンチャントの瓶",
#         name_jp="エンチャントの瓶",
#         call="エンチャントの瓶 (5コンボ！)",
#         game_id="trap_tower",
#         rank=5,
#     ),
#     KillingSpreeNoMedalState(rank=6),
#     KillingSpreeNoMedalState(rank=7),
#     KillingSpreeNoMedalState(rank=8),
#     KillingSpreeNoMedalState(rank=9),
#     KillingSpreeMedalState(
#         id_="trap_tower_merciless",
#         medal_image=image_path("trap_tower/merciless.png"),
#         name="Merciless",
#         name_jp="?",
#         game_id="trap_tower",
#         rank=10,
#     ),
#     KillingSpreeNoMedalState(rank=11),
#     KillingSpreeNoMedalState(rank=12),
#     KillingSpreeNoMedalState(rank=13),
#     KillingSpreeNoMedalState(rank=14),
#     KillingSpreeMedalState(
#         id_="trap_tower_ruthless",
#         medal_image=image_path("trap_tower/ruthless.png"),
#         name="Ruthless",
#         game_id="trap_tower",
#         rank=15,
#     ),
#     KillingSpreeNoMedalState(rank=16),
#     KillingSpreeNoMedalState(rank=17),
#     KillingSpreeNoMedalState(rank=18),
#     KillingSpreeNoMedalState(rank=19),
#     KillingSpreeMedalState(
#         id_="trap_tower_relentless",
#         medal_image=image_path("trap_tower/relentless.png"),
#         name="Relentless",
#         game_id="trap_tower",
#         rank=20,
#     ),
#     KillingSpreeNoMedalState(rank=21),
#     KillingSpreeNoMedalState(rank=22),
#     KillingSpreeNoMedalState(rank=23),
#     KillingSpreeNoMedalState(rank=24),
#     KillingSpreeMedalState(
#         id_="trap_tower_brutal",
#         medal_image=image_path("trap_tower/brutal.png"),
#         name="Brutal",
#         game_id="trap_tower",
#         rank=25,
#     ),
#     KillingSpreeNoMedalState(rank=26),
#     KillingSpreeNoMedalState(rank=27),
#     KillingSpreeNoMedalState(rank=28),
#     KillingSpreeNoMedalState(rank=29),
#     KillingSpreeMedalState(
#         id_="trap_tower_vicious",
#         medal_image=image_path("trap_tower/vicious.png"),
#         name="Vicious",
#         game_id="trap_tower",
#         rank=30,
#     ),
#     KillingSpreeMedalState(
#         id_="trap_tower_unstoppable",
#         medal_image=image_path("trap_tower/unstoppable.png"),
#         name="Unstoppable",
#         call="Unstoppable (shows every 5th earned)",
#         game_id="trap_tower",
#         rank=31,
#     ),
#     KillingSpreeMedalState(
#         id_="trap_tower_unstoppable",
#         medal_image=image_path("trap_tower/unstoppable.png"),
#         name="Unstoppable",
#         call="Unstoppable (shows every 5th earned)",
#         game_id="trap_tower",
#         rank=32,
#     ),
#     KillingSpreeMedalState(
#         id_="trap_tower_unstoppable",
#         medal_image=image_path("trap_tower/unstoppable.png"),
#         name="Unstoppable",
#         call="Unstoppable (shows every 5th earned)",
#         game_id="trap_tower",
#         rank=33,
#     ),
#     KillingSpreeMedalState(
#         id_="trap_tower_unstoppable",
#         medal_image=image_path("trap_tower/unstoppable.png"),
#         name="Unstoppable",
#         call="Unstoppable (shows every 5th earned)",
#         game_id="trap_tower",
#         rank=34,
#     ),
#     EndState(
#         KillingSpreeMedalState(
#             id_="trap_tower_unstoppable",
#             medal_image=image_path("trap_tower/unstoppable.png"),
#             name="Unstoppable",
#             call="Unstoppable (shows every 5th earned)",
#             game_id="trap_tower",
#             rank=35,
#         ),
#         index_to_return_to=31,
#     ),
# ]


trap_tower_layer3 = [
    EndState(
        KillingSpreeMedalState(
            id_="trap_tower_layer3_0",
            medal_image=image_path("halo_5/minecraft-bottle-o-enchanting.gif"),
            medal_sound=sound_path("orb"),
            name="Bottle o' Enchanting",
            name_jp="エンチャントの瓶",
            game_id="trap_tower",
            rank=0,
        ),
        index_to_return_to=0,
    )
]


@lru_cache
def get_all_displayable_medals():
    all_medals = itertools.chain(
        HALO_MULTIKILL_STATES,
        HALO_KILLING_SPREE_STATES,
        HALO_KILLSTREAK_STATES,
        MW2_KILLSTREAK_STATES,
        MW2_KILLING_SPREE_STATES,
        HALO_5_MULTIKILL_STATES,
        HALO_5_KILLING_SPREE_STATES,
        HALO_INFINITE_MULTIKILL_STATES,
        HALO_INFINITE_KILLING_SPREE_STATES,
        VANGUARD_MULTIKILL_STATES,
        VANGUARD_KILLING_SPREE_STATES,
        VANGUARD_KILLSTREAK_STATES,
        trap_tower_layer1,
        # trap_tower_layer_2,
        trap_tower_layer3,
    )
    return list(filter(lambda m: m.is_displayable_medal, all_medals))


def get_stores_by_game_id(config):
    return dict(
        halo_3=Store(
            state_machines=[
                InitialStreakState(
                    states=HALO_MULTIKILL_STATES,
                    interval_s=config["multikill_interval_s"],
                ),
                InitialStreakState(
                    states=HALO_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
                InitialStreakState(
                    states=HALO_KILLSTREAK_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        mw2=Store(
            state_machines=[
                InitialStreakState(
                    states=MW2_KILLSTREAK_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
                InitialStreakState(
                    states=MW2_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        halo_5=Store(
            state_machines=[
                InitialStreakState(
                    states=HALO_5_MULTIKILL_STATES,
                    interval_s=config["multikill_interval_s"],
                ),
                InitialStreakState(
                    states=HALO_5_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        halo_infinite=Store(
            state_machines=[
                InitialStreakState(
                    states=HALO_INFINITE_MULTIKILL_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
                InitialStreakState(
                    states=HALO_INFINITE_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        vanguard=Store(
            state_machines=[
                InitialStreakState(
                    states=VANGUARD_MULTIKILL_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
                InitialStreakState(
                    states=VANGUARD_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
                InitialStreakState(
                    states=VANGUARD_KILLSTREAK_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
        trap_tower=Store(
            state_machines=[
                InitialStreakState(
                    states=trap_tower_layer1,
                    interval_s=config["killing_spree_interval_s"],
                ),
                # InitialStreakState(
                #     states=trap_tower_layer_2,
                #     interval_s=config["killing_spree_interval_s"],
                # ),
                InitialStreakState(
                    states=trap_tower_layer3,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        ),
    )


def get_next_game_id(current_game_id):
    next_index = (all_game_ids.index(current_game_id) + 1) % len(all_game_ids)
    return all_game_ids[next_index]
