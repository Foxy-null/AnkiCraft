"""
AnkiCraft add-on

Copyright: (c) Foxy_null 2023 <https://github.com/Foxy-null>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from datetime import datetime, timedelta
from functools import lru_cache
import itertools
from os.path import join, dirname

from . import addons
from ._vendor import attr

DEFAULT_GAME_ID = "halo_3"
all_game_ids = ["halo_3", "mw2", "halo_5", "halo_infinite", "vanguard"]


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
            timedelta(seconds=min_interval_s)
            <= delta
            < timedelta(seconds=interval_s)
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
    medal_image = attr.ib()
    rank = attr.ib()
    game_id = attr.ib()
    _call = attr.ib(default=None)
    is_earnable_medal = attr.ib(default=True)
    is_displayable_medal = attr.ib(default=True)

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
    medal_image = attr.ib()
    rank = attr.ib()
    game_id = attr.ib()
    _call = attr.ib(default=None)
    is_displayable_medal = attr.ib(default=True)
    is_earnable_medal = attr.ib(default=True)


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
                m.on_answer(card_did_pass=card_did_pass)
                for m in self.state_machines
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

        return frozenset(
            medal for medal in all_medals if medal.is_displayable_medal
        )


class QuestionShownState:
    def __init__(
        self, states, question_shown_at, interval_s=8, current_streak_index=0, addon_is_installed_and_enabled=addons.is_installed_and_enabled
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
        if self._advancement_requirements_met(
            card_did_pass, self._answer_shown_at
        ):
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


    def _advancement_requirements_met(
        self, card_did_pass, question_answered_at
    ):
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
            current_streak_index=self.current_medal_state.next_streak_index(self._current_streak_index),
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


def image_path(filename):
    return join(images_dir, filename)


@attr.s(frozen=True)
class NewAchievement:
    medal = attr.ib()
    deck_id = attr.ib()

    @property
    def medal_id(self):
        return self.medal.id_

    @property
    def medal_name(self):
        return self.medal.name

    @property
    def medal_img_src(self):
        return self.medal.medal_image


HALO_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(),
    MultikillMedalState(
        id_="乾燥した昆布",
        medal_image=image_path("Dried_Kelp.webp"),
        name="Dried Kelp",
        game_id="halo_3",
        rank=2,
    ),
    MultikillMedalState(
        id_="石炭",
        medal_image=image_path("Coal.webp.png"),
        name="Coal",
        game_id="halo_3",
        rank=3,
    ),
    MultikillMedalState(
        id_="鉄インゴット",
        medal_image=image_path("Iron_ingot_0.webp.png"),
        name="Iron Ingot",
        game_id="halo_3",
        rank=4,
    ),
    MultikillMedalState(
        id_="レッドストーンダスト",
        medal_image=image_path("Redstone_Dust.webp.png"),
        name="Redstone Dust",
        game_id="halo_3",
        rank=5,
    ),
    MultikillMedalState(
        id_="ラピスラズリ",
        medal_image=image_path("Lapis_Lazuli.webp.png"),
        name="Lapis Lazuli",
        game_id="halo_3",
        rank=6,
    ),
    MultikillMedalState(
        id_="ダイヤモンド",
        medal_image=image_path("Diamond_0.webp.png"),
        name="Diamond",
        game_id="halo_3",
        rank=7,
    ),
    MultikillNoMedalState(rank=8),
    MultikillNoMedalState(rank=9),
    EndState(
        medal_state=MultikillMedalState(
            id_="エメラルド",
            medal_image=image_path("minecraft-block-of-emerald-and-emerald-cursor-pack.png"),
            name="Emerald",
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
        medal_image=image_path("Cobblestone.webp.png"),
        name="Cobblestone",
        game_id="halo_3",
        rank=1,
    ),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="矢",
        medal_image=image_path("Arrow.webp.png"),
        name="Arrow",
        game_id="halo_3",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="金のリンゴ",
        medal_image=image_path("Golden_Apple_JE2_BE2.webp.png"),
        name="Golden Apple",
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
        medal_image=image_path("Splash_Potion_of_Healing_JE2_BE2.webp.png"),
        name="Splash Potion of Healing II",
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
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="エンチャントされた金のリンゴ",
            medal_image=image_path("Enchanted_Golden_Apple_JE2_BE2.gif"),
            name="Enchanted Golden Apple",
            game_id="halo_3",
            rank=50,
        ),
        index_to_return_to=1
    ),
]

MW2_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="乾燥した昆布-1",
        medal_image=image_path("Dried_Kelp.webp"),
        name="Dried Kelp",
        game_id="mw2",
        rank=1,
        ),
    KillingSpreeMedalState(
        id_="砂",
        medal_image=image_path("mw2/Sand.webp.png"),
        name="Sand",
        game_id="mw2",
        #call="UAV recon standing by",
        rank=2,
    ),
    KillingSpreeMedalState(
        id_="砂岩",
        medal_image=image_path("mw2/Sandstone.webp.png"),
        name="Sandstone",
        game_id="mw2",
        #call="UAV recon standing by",
        rank=3,
    ),
    KillingSpreeMedalState(
        id_="粘土",
        medal_image=image_path("mw2/Clay.png"),
        name="Clay",
        game_id="mw2",
        #call="Care package waiting for your mark",
        rank=4,
    ),
    KillingSpreeMedalState(
        id_="焼き鱈",
        medal_image=image_path("mw2/Cooked_Cod_JE4_BE3.webp.png"),
        name="Cooked Cod",
        game_id="mw2",
        #call="Predator missile ready for launch",
        rank=5,
    ),
    KillingSpreeMedalState(
        id_="焼き鮭",
        medal_image=image_path("mw2/Cooked_Salmon.webp.png"),
        name="Cooked Salmon",
        game_id="mw2",
        #call="Airstrike standing by",
        rank=6,
    ),
    KillingSpreeMedalState(
        id_="ガラスブロック",
        medal_image=image_path("mw2/Glass.webp.png"),
        name="Glass",
        game_id="mw2",
        #call="Harrier's waiting for your mark",
        rank=7,
    ),
    KillingSpreeMedalState(
        id_="プリズマリンの欠片",
        medal_image=image_path("mw2/Prismarine_Shard.png"),
        name="Prismarine Shard",
        game_id="mw2",
        call="プリズマリンブロックをクラフト可能",
        rank=8,
    ),
    KillingSpreeMedalState(
        id_="プリズマリンクリスタル",
        medal_image=image_path("mw2/Prismarine_Crystal.png"),
        name="Prismarine Crystal",
        game_id="mw2",
        call="シーランタンをクラフト可能",
        rank=9,
    ),
EndState(
        medal_state=KillingSpreeMedalState(
            id_="TNTブロック",
            medal_image=image_path("mw2/TNT.webp.png"),
            name="TNT",
            game_id="mw2",
            rank=10,
        ),
        index_to_return_to=1,
    ),
    ]

HALO_5_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(),
    MultikillMedalState(
        id_="松明",
        medal_image=image_path("halo_5/Torch.webp.png"),
        name="Torch",
        game_id="halo_5",
        rank=2,
    ),
    MultikillMedalState(
        id_="オークの木材",
        medal_image=image_path("halo_5/Planks.webp.png"),
        name="Oak Planks",
        game_id="halo_5",
        rank=3,
    ),
    MultikillMedalState(
        id_="オークの原木-1",
        medal_image=image_path("halo_5/Oak_Log.webp.png"),
        name="Oak Log",
        game_id="halo_5",
        rank=4,
    ),
    MultikillMedalState(
        id_="白樺の原木-1",
        medal_image=image_path("halo_5/Birch_Log.webp.png"),
        name="Birch Log",
        game_id="halo_5",
        rank=5,
    ),
    MultikillMedalState(
        id_="ベイクドポテト",
        medal_image=image_path("halo_5/Baked_Potato_JE4_BE2.webp.png"),
        name="Baked Potato",
        game_id="halo_5",
        rank=6,
    ),
    MultikillMedalState(
        id_="ステーキ",
        medal_image=image_path("halo_5/SteakNew.webp.png"),
        name="Steak",
        game_id="halo_5",
        rank=7,
    ),
    MultikillMedalState(
        id_="エンダーパール",
        medal_image=image_path("halo_5/Ender_Pearl.png"),
        name="Ender Pearl",
        game_id="halo_5",
        rank=8,
    ),
    MultikillMedalState(
        id_="ロケット花火",
        medal_image=image_path("halo_5/minecraft-firework-rocket-and-firework-star-cursor.png"),
        name="Firework rocket",
        game_id="halo_5",
        rank=9,
    ),
    EndState(
        medal_state=MultikillMedalState(
            id_="金のリンゴ-1",
            medal_image=image_path("Golden_Apple_JE2_BE2.webp.png"),
            name="Golden Apple",
            game_id="halo_5",
            rank=10,
        ),
        index_to_return_to=2
    ),
]

HALO_5_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="土",
        medal_image=image_path("halo_5/Dirt.webp.png"),
        name="Dirt",
        game_id="halo_5",
        rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="矢-1",
        medal_image=image_path("Arrow.webp.png"),
        name="Arrow",
        game_id="halo_5",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="エンチャントの瓶",
        medal_image=image_path("halo_5/minecraft-bottle-o-enchanting.gif"),
        name="Bottle o' Enchanting",
        game_id="halo_5",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="鉄インゴット-1",
        medal_image=image_path("Iron_ingot_0.webp.png"),
        name="Iron Ingot",
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
            medal_image=image_path("halo_5/Totem_of_Undying_JE2_BE2.webp.png"),
            name="Totem of Undying",
            game_id="halo_5",
            rank=30,
        ),
        index_to_return_to=1
    ),
]


HALO_INFINITE_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(),
    MultikillMedalState(
        id_="スイカの薄切り",
        medal_image=image_path("halo_infinite/melon-slice.png"),
        name="Melon Slice",
        game_id="halo_infinite",
        rank=2,
    ),
    MultikillMedalState(
        id_="リンゴ",
        medal_image=image_path("halo_infinite/apple.png"),
        name="Apple",
        game_id="halo_infinite",
        rank=3,
    ),
    MultikillMedalState(
        id_="ニンジン",
        medal_image=image_path("halo_infinite/carrot.png"),
        name="Carrot",
        game_id="halo_infinite",
        rank=4,
    ),
    MultikillMedalState(
        id_="パン",
        medal_image=image_path("halo_infinite/bread.png"),
        name="Bread",
        game_id="halo_infinite",
        rank=5,
    ),
    MultikillMedalState(
        id_="クッキー",
        medal_image=image_path("halo_infinite/cookie.png"),
        name="Cookie",
        game_id="halo_infinite",
        rank=6,
    ),
    MultikillMedalState(
        id_="パンプキンパイ",
        medal_image=image_path("halo_infinite/pumpkin_pie.png"),
        name="Pumpkin Pie",
        game_id="halo_infinite",
        rank=7,
    ),
    MultikillMedalState(
        id_="グロウベリー",
        medal_image=image_path("halo_infinite/glow_berries.png"),
        name="Glow Berries",
        game_id="halo_infinite",
        rank=8,
    ),
    EndState(
        medal_state=MultikillMedalState(
            id_="ハチミツ入りの瓶",
            medal_image=image_path("halo_infinite/Honey_Bottle_JE1_BE2.webp.png"),
            name="Honey Bottle",
            game_id="halo_infinite",
            rank=9,
        ),
        index_to_return_to=2
    ),
]


HALO_INFINITE_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="スイートベリー",
        medal_image=image_path("halo_infinite/sweet-berries.png"),
        name="Sweet Berries",
        game_id="halo_infinite",
        rank=1,
),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="焼き鳥",
        medal_image=image_path("halo_infinite/Cooked_Chicken_JE3_BE3.webp.png"),
        name="Cooked Chicken",
        game_id="halo_infinite",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="焼き豚",
        medal_image=image_path("halo_infinite/Cooked_Porkchop_JE4_BE3.webp.png"),
        name="Cooked Porkchop",
        game_id="halo_infinite",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="金のリンゴ-2",
        medal_image=image_path("Golden_Apple_JE2_BE2.webp.png"),
        name="Golden Apple",
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
            medal_image=image_path("Enchanted_Golden_Apple_JE2_BE2.gif"),
            name="Enchanted Golden Apple",
            game_id="halo_infinite",
            rank=20,
        ),
        index_to_return_to=11
    ),
]


VANGUARD_MULTIKILL_STATES = [
    MultikillStartingState(),
    EndState(
        medal_state=MultikillMedalState(
            id_="オークの原木",
            medal_image=image_path("halo_5/Oak_Log.webp.png"),
            name="Oak Log",
            game_id="vanguard",
            rank=1,
        ),
        index_to_return_to=1
    ),
]


VANGUARD_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeMedalState(
        id_="白樺の原木",
        medal_image=image_path("vanguard/Birch_Log.webp.png"),
        name="Birch Log",
        game_id="vanguard",
        rank=1,
    ),
    KillingSpreeMedalState(
        id_="トウヒの原木",
        medal_image=image_path("vanguard/Spruce_Log.webp.png"),
        name="Spruce Log",
        game_id="vanguard",
        rank=2,
    ),
    KillingSpreeMedalState(
        id_="ダークオークの原木",
        medal_image=image_path("vanguard/Dark_Oak_Log.png"),
        name="Dark Oak Log",
        game_id="vanguard",
        rank=3,
    ),
    KillingSpreeMedalState(
        id_="ジャングルの原木",
        medal_image=image_path("vanguard/Jungle_Log.webp.png"),
        name="Jungle Log",
        game_id="vanguard",
        rank=4,
    ),
    KillingSpreeMedalState(
        id_="アカシアの原木",
        medal_image=image_path("vanguard/Acacia_Log.png"),
        name="Acacia Log",
        game_id="vanguard",
        rank=5,
    ),
    KillingSpreeMedalState(
        id_="マングローブの原木",
        medal_image=image_path("vanguard/Mangrove_Log.png"),
        name="Mangrove Log",
        game_id="vanguard",
        rank=6,
    ),
    KillingSpreeMedalState(
        id_="サクラの原木",
        medal_image=image_path("vanguard/Cherry_Log.png"),
        name="Cherry Log",
        game_id="vanguard",
        rank=7,
    ),
    KillingSpreeMedalState(
        id_="リンゴ-1",
        medal_image=image_path("halo_infinite/apple.png"),
        name="Apple",
        game_id="vanguard",
        rank=8,
    ),
    KillingSpreeMedalState(
        id_="歪んだ原木",
        medal_image=image_path("vanguard/Warped_Stem.png"),
        name="Warped Stem",
        game_id="vanguard",
        rank=9,
    ),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="真紅の原木",
            medal_image=image_path("vanguard/Crimson_Stem.png"),
            name="Crimson Stem",
            game_id="vanguard",
            rank=10,
        ),
        index_to_return_to=1
    ),
]


VANGUARD_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeMedalState(
        id_="茶色のキノコ",
        medal_image=image_path("vanguard/BrownMushroomNew.webp.png"),
        name="Brown Mushroom",
        game_id="vanguard",
        rank=3,
    ),
    EndState(
        medal_state=KillingSpreeMedalState(
            id_="赤色のキノコ",
            medal_image=image_path("vanguard/RedMushroomNew.webp.png"),
            name="Red Mushroom",
            game_id="vanguard",
            rank=4,
        ),
        index_to_return_to=1,
    ),
]


MWR_MULTIKILL_STATES = [
    MultikillStartingState(),
    MultikillNoMedalState(rank=1),
    MultikillMedalState(
        id_="mwr_double_kill",
        medal_image=image_path("mwr/double-kill.png"),
        name="Double Kill",
        game_id="mwr",
        rank=2,
    ),
    MultikillMedalState(
        id_="mwr_triple_kill",
        medal_image=image_path("mwr/triple-kill.png"),
        name="Triple Kill",
        game_id="mwr",
        rank=3,
    ),
    MultikillMedalState(
        id_="mwr_fury_kill",
        medal_image=image_path("mwr/fury-kill.png"),
        name="Fury Kill",
        game_id="mwr",
        rank=4,
    ),
    MultikillMedalState(
        id_="mwr_frenzy_kill",
        medal_image=image_path("mwr/frenzy-kill.png"),
        name="Frenzy Kill",
        game_id="mwr",
        rank=5,
    ),
    MultikillMedalState(
        id_="mwr_super_kill",
        medal_image=image_path("mwr/super-kill.png"),
        name="Super Kill",
        game_id="mwr",
        rank=6,
    ),
    MultikillMedalState(
        id_="mwr_mega_kill",
        medal_image=image_path("mwr/mega-kill.png"),
        name="Mega Kill",
        game_id="mwr",
        rank=7,
    ),
    MultikillMedalState(
        id_="mwr_ultra_kill",
        medal_image=image_path("mwr/ultra-kill.png"),
        name="Ultra Kill",
        game_id="mwr",
        rank=8,
    ),
    MultikillMedalState(
        id_="mwr_kill_chain",
        medal_image=image_path("mwr/kill-chain.png"),
        name="Kill Chain",
        call="Kill Chain (shows every 5th earned)",
        game_id="mwr",
        rank=9,
    ),
    MultikillMedalState(
        id_="mwr_kill_chain",
        medal_image=image_path("mwr/kill-chain.png"),
        name="Kill Chain",
        call="Kill Chain (shows every 5th earned)",
        game_id="mwr",
        rank=10,
    ),
    MultikillMedalState(
        id_="mwr_kill_chain",
        medal_image=image_path("mwr/kill-chain.png"),
        name="Kill Chain",
        call="Kill Chain (shows every 5th earned)",
        game_id="mwr",
        rank=11,
    ),
    MultikillMedalState(
        id_="mwr_kill_chain",
        medal_image=image_path("mwr/kill-chain.png"),
        name="Kill Chain",
        call="Kill Chain (shows every 5th earned)",
        game_id="mwr",
        rank=12,
    ),
    EndState(
        MultikillMedalState(
            id_="mwr_kill_chain",
            medal_image=image_path("mwr/kill-chain.png"),
            name="Kill Chain",
            call="Kill Chain (shows every 5th earned)",
            game_id="mwr",
            rank=13,
        ),
        index_to_return_to=9
    ),
]


MWR_KILLING_SPREE_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeNoMedalState(rank=3),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="mwr_bloodthirsty",
        medal_image=image_path("mwr/bloodthirsty.png"),
        name="Bloodthirsty",
        game_id="mwr",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    KillingSpreeNoMedalState(rank=7),
    KillingSpreeNoMedalState(rank=8),
    KillingSpreeNoMedalState(rank=9),
    KillingSpreeMedalState(
        id_="mwr_merciless",
        medal_image=image_path("mwr/merciless.png"),
        name="Merciless",
        game_id="mwr",
        rank=10,
    ),
    KillingSpreeNoMedalState(rank=11),
    KillingSpreeNoMedalState(rank=12),
    KillingSpreeNoMedalState(rank=13),
    KillingSpreeNoMedalState(rank=14),
    KillingSpreeMedalState(
        id_="mwr_ruthless",
        medal_image=image_path("mwr/ruthless.png"),
        name="Ruthless",
        game_id="mwr",
        rank=15,
    ),
    KillingSpreeNoMedalState(rank=16),
    KillingSpreeNoMedalState(rank=17),
    KillingSpreeNoMedalState(rank=18),
    KillingSpreeNoMedalState(rank=19),
    KillingSpreeMedalState(
        id_="mwr_relentless",
        medal_image=image_path("mwr/relentless.png"),
        name="Relentless",
        game_id="mwr",
        rank=20,
    ),
    KillingSpreeNoMedalState(rank=21),
    KillingSpreeNoMedalState(rank=22),
    KillingSpreeNoMedalState(rank=23),
    KillingSpreeNoMedalState(rank=24),
    KillingSpreeMedalState(
        id_="mwr_brutal",
        medal_image=image_path("mwr/brutal.png"),
        name="Brutal",
        game_id="mwr",
        rank=25,
    ),
    KillingSpreeNoMedalState(rank=26),
    KillingSpreeNoMedalState(rank=27),
    KillingSpreeNoMedalState(rank=28),
    KillingSpreeNoMedalState(rank=29),
    KillingSpreeMedalState(
        id_="mwr_vicious",
        medal_image=image_path("mwr/vicious.png"),
        name="Vicious",
        game_id="mwr",
        rank=30,
    ),
    KillingSpreeMedalState(
        id_="mwr_unstoppable",
        medal_image=image_path("mwr/unstoppable.png"),
        name="Unstoppable",
        call="Unstoppable (shows every 5th earned)",
        game_id="mwr",
        rank=31,
    ),
    KillingSpreeMedalState(
        id_="mwr_unstoppable",
        medal_image=image_path("mwr/unstoppable.png"),
        name="Unstoppable",
        call="Unstoppable (shows every 5th earned)",
        game_id="mwr",
        rank=32,
    ),
    KillingSpreeMedalState(
        id_="mwr_unstoppable",
        medal_image=image_path("mwr/unstoppable.png"),
        name="Unstoppable",
        call="Unstoppable (shows every 5th earned)",
        game_id="mwr",
        rank=33,
    ),
    KillingSpreeMedalState(
        id_="mwr_unstoppable",
        medal_image=image_path("mwr/unstoppable.png"),
        name="Unstoppable",
        call="Unstoppable (shows every 5th earned)",
        game_id="mwr",
        rank=34,
    ),
    EndState(
        KillingSpreeMedalState(
            id_="mwr_unstoppable",
            medal_image=image_path("mwr/unstoppable.png"),
            name="Unstoppable",
            call="Unstoppable (shows every 5th earned)",
            game_id="mwr",
            rank=35,
        ),
        index_to_return_to=31,
    )
]


MWR_KILLSTREAK_STATES = [
    KillingSpreeNoMedalState(rank=0),
    KillingSpreeNoMedalState(rank=1),
    KillingSpreeNoMedalState(rank=2),
    KillingSpreeMedalState(
        id_="mwr_radar",
        medal_image=image_path("mwr/radar.png"),
        name="Radar",
        game_id="mwr",
        rank=3,
    ),
    KillingSpreeNoMedalState(rank=4),
    KillingSpreeMedalState(
        id_="mwr_airstrike",
        medal_image=image_path("mwr/airstrike.png"),
        name="Airstrike",
        game_id="mwr",
        rank=5,
    ),
    KillingSpreeNoMedalState(rank=6),
    EndState(
        KillingSpreeMedalState(
            id_="mwr_helicopter",
            medal_image=image_path("mwr/helicopter.png"),
            name="Helicopter",
            game_id="mwr",
            rank=7,
        ),
        index_to_return_to=1,
    ),
]


@lru_cache
def get_all_displayable_medals():
    all_medals = itertools.chain(
        HALO_MULTIKILL_STATES,
        HALO_KILLING_SPREE_STATES,
        MW2_KILLSTREAK_STATES,
        HALO_5_MULTIKILL_STATES,
        HALO_5_KILLING_SPREE_STATES,
        HALO_INFINITE_MULTIKILL_STATES,
        HALO_INFINITE_KILLING_SPREE_STATES,
        VANGUARD_MULTIKILL_STATES,
        VANGUARD_KILLING_SPREE_STATES,
        VANGUARD_KILLSTREAK_STATES,
        MWR_MULTIKILL_STATES,
        MWR_KILLING_SPREE_STATES,
        MWR_KILLSTREAK_STATES,
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
            ]
        ),
        mw2=Store(
            state_machines=[
                InitialStreakState(
                    states=MW2_KILLSTREAK_STATES,
                    interval_s=config["killing_spree_interval_s"],
                )
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
                    interval_s=config["killing_spree_interval_s"]
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
                    interval_s=config["killing_spree_interval_s"]
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
        mwr=Store(
            state_machines=[
                InitialStreakState(
                    states=MWR_MULTIKILL_STATES,
                    interval_s=config["killing_spree_interval_s"]
                ),
                InitialStreakState(
                    states=MWR_KILLING_SPREE_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
                InitialStreakState(
                    states=MWR_KILLSTREAK_STATES,
                    interval_s=config["killing_spree_interval_s"],
                ),
            ]
        )
    )


def get_next_game_id(current_game_id):
    next_index = (all_game_ids.index(current_game_id) + 1) % len(all_game_ids)
    return all_game_ids[next_index]
