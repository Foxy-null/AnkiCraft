# -*- coding: utf-8 -*-
"""
Original Copyright/License statement
------
Anki Add-on: Puppy Reinforcement

Uses intermittent reinforcement to encourage card review streaks

Copyright: (c) Glutanimate 2016-2018 <https://glutanimate.com/>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
------

Modifications by jac241 <https://github.com/jac241> for Anki Killstreaks addon
Customized by Foxy_null <https://github.com/Foxy-null> for AnkiCraft addon
"""

from datetime import datetime, timedelta
from functools import partial, wraps
import os
from pathlib import Path
from queue import Queue
from threading import Thread
from urllib.parse import urljoin
import aqt.sound

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.deckbrowser import DeckBrowser
from aqt.reviewer import Reviewer
from aqt.sound import play, clearAudioQueue, av_player
from anki.sound import AV_REF_RE, AVTag, SoundOrVideoTag
from aqt.overview import Overview
from anki.hooks import addHook, wrap
from anki.stats import CollectionStats
from .config import local_conf
from .controllers import (
    ProfileController,
    build_on_answer_wrapper,
    call_method_on_object_from_factory_function,
)
from .networking import process_queue, stop_thread_on_app_close
from .persistence import day_start_time, min_datetime
from ._vendor import attr

from .views import (
    MedalsOverviewHTML,
    TodaysMedalsJS,
    TodaysMedalsForDeckJS,
    js_content,
)
from .streaks import get_stores_by_game_id

TMJS = TodaysMedalsJS

from .streaks import get_stores_by_game_id
from .menu import connect_menu


def show_tool_tip_if_medals(displayable_medals):
    if len(displayable_medals) > 0:
        showToolTip(displayable_medals)


def _get_profile_folder_path(profile_manager=mw.pm):
    folder = profile_manager.profileFolder()
    return Path(folder)


_stores_by_game_id = get_stores_by_game_id(config=local_conf)

job_queue = Queue()
_network_thread = Thread(target=process_queue, args=(job_queue,), daemon=True)
stop_thread_on_app_close(app=QApplication.instance(), queue=job_queue)


_profile_controller = ProfileController(
    local_conf=local_conf,
    show_achievements=show_tool_tip_if_medals,
    get_profile_folder_path=_get_profile_folder_path,
    stores_by_game_id=_stores_by_game_id,
    job_queue=job_queue,
    main_window=mw,
)

# for debugging
mw.killstreaks_profile_controller = _profile_controller


def main():
    _wrap_anki_objects(_profile_controller)
    connect_menu(
        main_window=mw, profile_controller=_profile_controller, network_thread=job_queue
    )
    _network_thread.start()


def _wrap_anki_objects(profile_controller):
    """
    profileLoaded hook fired after deck broswer gets shown(???), so we can't
    actually rely on that hook for anything... To get around this,
    made a decorator that I'll decorate any method that uses the profile
    controller to make sure it's loaded
    """
    addHook("unloadProfile", profile_controller.unload_profile)

    # Need to make sure we call these methods on the current reviewing controller.
    # Reviewing controller instance changes when profile changes.
    call_method_on_reviewing_controller = partial(
        call_method_on_object_from_factory_function,
        factory_function=profile_controller.get_reviewing_controller,
    )

    addHook("showQuestion", call_method_on_reviewing_controller("on_show_question"))
    addHook("showAnswer", call_method_on_reviewing_controller("on_show_answer"))

    Reviewer._answerCard = wrap(
        Reviewer._answerCard,
        partial(
            build_on_answer_wrapper,
            on_answer=call_method_on_reviewing_controller("on_answer"),
        ),
        "before",
    )

    if local_conf["WhereToShowMedals"] == "disabled":
        pass
    elif local_conf["WhereToShowMedals"] == "oldstat":
        todays_medals_injector = partial(
            inject_medals_with_js,
            view=TMJS,
            get_achievements_repo=profile_controller.get_achievements_repo,
            get_current_game_id=profile_controller.get_current_game_id,
        )
        CollectionStats.todayStats = wrap(
            old=CollectionStats.todayStats,
            new=partial(
                show_medals_overview,
                get_achievements_repo=profile_controller.get_achievements_repo,
                get_current_game_id=profile_controller.get_current_game_id,
            ),
            pos="around",
        )

    else:
        CollectionStats.todayStats = wrap(
            old=CollectionStats.todayStats,
            new=partial(
                show_medals_overview,
                get_achievements_repo=profile_controller.get_achievements_repo,
                get_current_game_id=profile_controller.get_current_game_id,
            ),
            pos="around",
        )

        todays_medals_injector = partial(
            inject_medals_with_js,
            view=TMJS,
            get_achievements_repo=profile_controller.get_achievements_repo,
            get_current_game_id=profile_controller.get_current_game_id,
        )

        # 修正ここから -----
        from anki.utils import pointVersion

        if pointVersion() >= 231000:  # gui_hooksに変更

            gui_hooks.deck_browser_did_render.remove(
                todays_medals_injector
            )  # profile変更後の重複を避ける
            gui_hooks.deck_browser_did_render.append(todays_medals_injector)

            overview_medals_injector = partial(
                inject_medals_for_deck_overview,
                get_achievements_repo=profile_controller.get_achievements_repo,
                get_current_game_id=profile_controller.get_current_game_id,
            )

            gui_hooks.overview_did_refresh.remove(overview_medals_injector)
            gui_hooks.overview_did_refresh.append(overview_medals_injector)
            # 修正ここまで -----

        else:  # 古いwrap
            DeckBrowser.refresh = wrap(
                old=DeckBrowser.refresh, new=todays_medals_injector, pos="after"
            )

            DeckBrowser.show = wrap(
                old=DeckBrowser.show, new=todays_medals_injector, pos="after"
            )

            Overview.refresh = wrap(
                old=Overview.refresh,
                new=partial(
                    inject_medals_for_deck_overview,
                    get_achievements_repo=profile_controller.get_achievements_repo,
                    get_current_game_id=profile_controller.get_current_game_id,
                ),
                pos="after",
            )


_tooltipTimer = None
_tooltipLabel = None
sfx: list[AVTag] = []


def _pop_next():
    if not sfx:
        return None
    return sfx.pop(0)


def _play_next_if_idle() -> None:
    if av_player.current_player:
        return
    next = _pop_next()
    if next is not None:
        _play(next)
    else:
        aqt.sound.av_player.interrupt_current_audio = True
        av_player._play_next_if_idle()


def insert_file(filename: str) -> None:
    if filename is not None and os.path.exists(
        filename
    ):  # filenameがNoneでなく、ファイルが存在するかどうかチェック
        sfx.insert(len(sfx), SoundOrVideoTag(filename=filename))
        _play_next_if_idle()


def _play(tag: AVTag) -> None:
    best_player = av_player._best_player_for_tag(tag)
    if best_player:
        av_player.current_player = best_player
        gui_hooks.av_player_will_play(tag)
        av_player.current_player.play(tag, _on_play_finished)


def _on_play_finished() -> None:
    gui_hooks.av_player_did_end_playing(av_player.current_player)
    av_player.current_player = None
    _play_next_if_idle()


def play_sound(sound):
    mw.progress.single_shot(0, lambda: _play(sound), True)


def showToolTip(medals, period=local_conf["duration"]):
    global _tooltipTimer, _tooltipLabel

    if local_conf["play_sound"] == "false":
        pass
    else:
        av_player.stop_and_clear_queue()
        aqt.sound.av_player.interrupt_current_audio = False
        for m in medals:
            insert_file(m.medal_sound)
        next = _pop_next()
        if next is not None:
            play_sound(next)

    class CustomLabel(QLabel):
        def mousePressEvent(self, evt):
            evt.accept()
            self.hide()

    closeTooltip()
    medals_html = "\n".join(medal_html(m) for m in medals)

    aw = mw.app.activeWindow() or mw
    lab = CustomLabel(
        """\
<table cellpadding=10>
<tr>
%s
</tr>
</table>"""
        % (medals_html),
        aw,
    )
    lab.setFrameStyle(QFrame.Shape.Panel)
    lab.setLineWidth(2)
    lab.setWindowFlags(Qt.WindowType.ToolTip)
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(local_conf["tooltip_color"]))
    p.setColor(QPalette.ColorRole.WindowText, QColor("#f7f7f7"))
    lab.setPalette(p)
    vdiff = (local_conf["image_height"] - 128) / 2
    lab.move(aw.mapToGlobal(QPoint(0, -260 - vdiff + aw.height())))
    lab.show()
    _tooltipTimer = mw.progress.timer(period, closeTooltip, False)
    _tooltipLabel = lab


def closeTooltip():
    global _tooltipLabel, _tooltipTimer
    if _tooltipLabel:
        try:
            _tooltipLabel.deleteLater()
        except:
            # already deleted as parent window closed
            pass
        _tooltipLabel = None
    if _tooltipTimer:
        _tooltipTimer.stop()
        _tooltipTimer = None


if local_conf["show_image_on_tooltip"] == "false":

    def medal_html(medal):
        return """
            <td valign="middle" style="text-align:center">
                <center><b>{call} ×1</b></center>
            </td>
        """.format(
            call=medal.call,
        )

else:

    def medal_html(medal):
        global sfx_src
        sfx_src = medal.medal_sound
        return """
            <td valign="middle" style="text-align:center">
                <img src="{img_src}">
                <center><b>{call} ×1</b><br></center>
            </td>
        """.format(
            img_src=medal.medal_image,
            call=medal.call,
        )


def inject_medals_with_js(
    self: Overview, get_achievements_repo, get_current_game_id, view
):
    self.mw.web.eval(
        view(
            achievements=get_achievements_repo().todays_achievements(
                cutoff_datetime(self)
            ),
            current_game_id=get_current_game_id(),
        )
    )
    self.mw.web.eval(js_content("medals_overview.js"))


def inject_medals_for_deck_overview(
    self: Overview,
    get_achievements_repo,
    get_current_game_id,
):
    decks = get_current_deck_and_children(deck_manager=self.mw.col.decks)
    deck_ids = [d.id_ for d in decks]

    self.mw.web.eval(
        TodaysMedalsForDeckJS(
            achievements=get_achievements_repo().todays_achievements_for_deck_ids(
                day_start_time=cutoff_datetime(self), deck_ids=deck_ids
            ),
            deck=decks[0],
            current_game_id=get_current_game_id(),
        )
    )
    self.mw.web.eval(js_content("medals_overview.js"))


@attr.s
class Deck:
    id_ = attr.ib()
    name = attr.ib()


def get_current_deck_and_children(deck_manager):
    current_deck_attrs = deck_manager.current()

    current_deck = Deck(current_deck_attrs["id"], current_deck_attrs["name"])
    children = [
        Deck(name=name_id_pair[0], id_=name_id_pair[1])
        for name_id_pair in deck_manager.children(current_deck.id_)
    ]

    return [current_deck, *children]


def show_medals_overview(
    self: CollectionStats,
    _old,
    get_achievements_repo,
    get_current_game_id,
):
    current_deck = self.col.decks.current()["name"]

    header_text = _get_stats_header(
        deck_name=current_deck,
        scope_is_whole_collection=self.wholeCollection,
        period=self.type,
    )

    deck_ids = [d.id_ for d in get_current_deck_and_children(self.col.decks)]

    achievements = _get_achievements_scoped_to_deck_or_collection(
        deck_ids=deck_ids,
        scope_is_whole_collection=self.wholeCollection,
        achievements_repo=get_achievements_repo(),
        start_datetime=_get_start_datetime_for_period(self.type),
    )

    return _old(self) + MedalsOverviewHTML(
        achievements=achievements,
        header_text=header_text,
        current_game_id=get_current_game_id(),
    )


if local_conf["language"] == "ja":

    def _get_stats_header(deck_name, scope_is_whole_collection, period):
        scope_name = (
            "コレクション全体" if scope_is_whole_collection else f"「{deck_name}」内"
        )
        time_period_description = _get_time_period_description(period)
        return f"{scope_name}で{time_period_description}に獲得したアイテム"

else:

    def _get_stats_header(deck_name, scope_is_whole_collection, period):
        scope_name = (
            "your whole collection"
            if scope_is_whole_collection
            else f'deck "{deck_name}"'
        )
        time_period_description = _get_time_period_description(period)
        return f"All unclaimed items in {scope_name} {time_period_description}:"


PERIOD_MONTH = 0
PERIOD_YEAR = 1

if local_conf["language"] == "ja":

    def _get_time_period_description(period):
        if period == PERIOD_MONTH:
            return "過去１ヶ月"
        elif period == PERIOD_YEAR:
            return "過去１年"
        else:
            return "今まで"

else:

    def _get_time_period_description(period):
        if period == PERIOD_MONTH:
            return "over the past month"
        elif period == PERIOD_YEAR:
            return "over the past year"
        else:
            return "over the deck's life"


def _get_start_datetime_for_period(period):
    if period == PERIOD_MONTH:
        return datetime.now() - timedelta(days=30)
    elif period == PERIOD_YEAR:
        return datetime.now() - timedelta(days=365)
    else:
        return min_datetime


def _get_achievements_scoped_to_deck_or_collection(
    deck_ids, scope_is_whole_collection, achievements_repo, start_datetime
):
    if scope_is_whole_collection:
        return achievements_repo.achievements_for_whole_collection_since(
            since_datetime=start_datetime
        )
    else:
        return achievements_repo.achievements_for_deck_ids_since(
            deck_ids=deck_ids, since_datetime=start_datetime
        )


def cutoff_datetime(self):
    return day_start_time(rollover_hour=self.mw.col.conf.get("rollover", 4))


main()
