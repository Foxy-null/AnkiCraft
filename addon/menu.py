from functools import partial
from aqt.qt import QMenu
from aqt.qt import QMessageBox
from .config import local_conf
from .persistence import min_datetime
import random
from ._vendor import pyperclip

from .game import (
    load_current_game_id,
    set_current_game_id,
    toggle_auto_switch_game,
    load_auto_switch_game_status,
)

from . import profile_settings, networking

if local_conf["language"] == "ja":
    automatically_switch_games = "&バイオーム自動切り替え"
    change_biome = "バイオームを選ぶ"
    cave_name = "洞窟"
    ocean_name = "海バイオーム"
    overworld_name = "草原バイオーム"
    farm_name = "食料畑"
    forest_name = "森林バイオーム"
    trap_tower_name = "トラップタワー"
    claim_items_name = "アイテムを回収する（Java版のみ）"
    claim_items_box_text = "アイテムを全て削除するには「リセット」をクリックして下さい。"
    claim_items_deleted_text = "削除が完了しました。変更を適用するには画面を開き直してください。"
    claim_items_box_text_no_items = "回収できるアイテムがありません"
    claim_items_next_command_text = "上記のコマンドがクリップボードにコピーされました。\n次のコマンドを表示するには[OK]を押してください。" 
else:
    automatically_switch_games = "&Automatically Switch Games"
    change_biome = "Change Biome"
    cave_name = "Cave"
    ocean_name = "Ocean"
    overworld_name = "Overworld"
    farm_name = "Farm"
    forest_name = "Forest"
    trap_tower_name = "Trap Tower"
    claim_items_name = "Claim Items (Java edition only)"
    claim_items_box_text = "Click reset to clear the unclaimed items"
    claim_items_deleted_text = "Deleted, You may have to refresh your screen by changing tabs"
    claim_items_box_text_no_items = "No items to claim"
    claim_items_next_command_text = "The above command has been copied to the clipboard.\nPress ok to display next command"

def connect_menu(main_window, profile_controller, network_thread):
    # probably overdoing it with partial functions here... but none of these
    # need to be classes honestly
    top_menu = QMenu("Anki&Craft", main_window)
    game_menu = QMenu(change_biome, main_window)

    halo_3_action = game_menu.addAction(cave_name)
    halo_3_action.setCheckable(True)
    halo_3_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="halo_3",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    mw2_action = game_menu.addAction(ocean_name)
    mw2_action.setCheckable(True)
    mw2_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="mw2",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    halo_5_action = game_menu.addAction(overworld_name)
    halo_5_action.setCheckable(True)
    halo_5_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="halo_5",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )
    halo_infinite_action = game_menu.addAction(farm_name)
    halo_infinite_action.setCheckable(True)
    halo_infinite_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="halo_infinite",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    vanguard_action = game_menu.addAction(forest_name)
    vanguard_action.setCheckable(True)
    vanguard_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="vanguard",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    trap_tower_action = game_menu.addAction(trap_tower_name)
    trap_tower_action.setCheckable(True)
    trap_tower_action.triggered.connect(
        partial(
            set_current_game_id,
            game_id="trap_tower",
            get_settings_repo=profile_controller.get_settings_repo,
            on_game_changed=profile_controller.change_game,
        )
    )

    top_menu.addMenu(game_menu)

    game_menu.aboutToShow.connect(
        partial(
            check_correct_game_in_menu,
            menu_actions_by_game_id=dict(
                halo_3=halo_3_action,
                mw2=mw2_action,
                halo_5=halo_5_action,
                halo_infinite=halo_infinite_action,
                vanguard=vanguard_action,
                trap_tower=trap_tower_action,
            ),
            load_current_game_id=partial(
                load_current_game_id,
                get_settings_repo=profile_controller.get_settings_repo,
            ),
        )
    )

    auto_switch_game_action = top_menu.addAction(automatically_switch_games)
    auto_switch_game_action.setCheckable(True)
    auto_switch_game_action.triggered.connect(
        partial(
            toggle_auto_switch_game,
            get_settings_repo=profile_controller.get_settings_repo,
            on_auto_switch_game_toggled=profile_controller.on_auto_switch_game_toggled,
        )
    )
    top_menu.aboutToShow.connect(
        partial(
            set_check_for_auto_switch_game,
            action=auto_switch_game_action,
            load_auto_switch_game_status=partial(
                load_auto_switch_game_status,
                get_settings_repo=profile_controller.get_settings_repo,
            ),
        )
    )

    # Claim Items Button
    claim_items_game_action = top_menu.addAction(claim_items_name)
    claim_items_game_action.triggered.connect(
        partial(
            show_give_item_popup,
            profile_controller = profile_controller
        )
    )
    

    main_window.form.menubar.addMenu(top_menu)


def check_correct_game_in_menu(menu_actions_by_game_id, load_current_game_id):
    current_game_id = load_current_game_id()

    for game_id, action in menu_actions_by_game_id.items():
        if game_id == current_game_id:
            action.setChecked(True)
        else:
            action.setChecked(False)


def set_check_for_auto_switch_game(action, load_auto_switch_game_status):
    action.setChecked(load_auto_switch_game_status())

def show_give_item_popup(profile_controller):

    commands = get_item_command(profile_controller)

    # Check if there are any commands
    if(len(commands) <= 0):
        msg = QMessageBox()
        msg.setText(claim_items_box_text_no_items)
        msg.setWindowTitle(claim_items_name)
        msg.setStandardButtons(QMessageBox.StandardButton.Abort)
        return

    retval = QMessageBox.StandardButton.Ok

    command_index = 0
    for command in commands:
        command_index += 1;
        msg = QMessageBox()
        msg.setText(f"{command}"+"\n"+claim_items_next_command_text+f" ({command_index}/{len(commands)})")
        msg.setWindowTitle(claim_items_name)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Abort)
        pyperclip.copy(command)
        retval = msg.exec() 

        # check for abort clicked
        if(retval != QMessageBox.StandardButton.Ok):
            return

    # Ask user if they want database reset
    msg2 = QMessageBox()
    msg2.setText(claim_items_box_text)
    msg2.setWindowTitle(claim_items_name)
    msg2.setStandardButtons(QMessageBox.StandardButton.Reset | QMessageBox.StandardButton.Abort)
    retval = msg2.exec() 

    if(retval == QMessageBox.StandardButton.Reset):
        profile_controller.get_achievements_repo().clear_achievements()

        msg3 = QMessageBox()
        msg3.setText(claim_items_deleted_text)
        msg3.setWindowTitle(claim_items_name)
        msg3.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg3.exec() 

SPECIAL_ITEMS = ["healing_potion_ii", "random_firework"]
def get_special_item_command(id, count):
    username = local_conf["minecraft_username"]
    final_count = 0 if count <= 6400 else count - 6400
    cmd_count = min(count, 6400)
    
    if(id == "healing_potion_ii"):
        # recalulate the max counts because minecraft wont let you /give more than 100 potions
        # good luck to anyone who has earned thousands of potions because they're gonna have to
        # run alot of commands
        final_count = 0 if count <= 100 else count - 100
        cmd_count = min(count, 100)

        # Supports bedrock
        if(local_conf["is_bedrock_edition"] == "true"):
            return f'/give {username} splash_potion {cmd_count} 22', final_count

        # Supports 1.20.6
        if(local_conf["minecraft_version_is_pre_1_20_5"] == "false"):
            return f'/give {username} splash_potion[potion_contents={{potion:"strong_healing"}}] {cmd_count}', final_count
        
        # Supports between 1.13 and 1.20.5
        return f'/give {username} splash_potion{{Potion:"minecraft:strong_healing"}} {cmd_count}', final_count
    
    if(id == "random_firework"):
        # random varibles
        colour = random.randrange(0, 16777215) # random hex colour in decimal form
        fade_colour = random.randrange(0, 16777215) # random hex colour in decimal form
        flight_time = random.randrange(0, 5) # random flight time
        shape = random.randrange(0, 4)
        has_trail = random.choice([0, 1])
        has_twinkle = random.choice([0, 1])

        # Supports bedrock
        if(local_conf["is_bedrock_edition"] == "true"):
            return f'/give {username} firework_rocket {cmd_count} 0', final_count

        # Supports 1.20.6
        if(local_conf["minecraft_version_is_pre_1_20_5"] == "false"):
            shape = random.choice(["small_ball", "large_ball", "star", "creeper", "burst"])
            has_trail = random.choice(["true", "false"])
            has_twinkle = random.choice(["true", "false"])

            return f'/give {username} firework_rocket[fireworks={{explosions:[{{shape:"{shape}",colors:[{colour}],colors:[{fade_colour}],has_trail:{has_trail},has_twinkle:{has_twinkle}}}],flight_duration:{flight_time}}}] {cmd_count}', final_count
        
        return f'/give {username} firework_rocket{{Fireworks:{{Flight:{flight_time},Explosions:[{{Type:{shape},Flicker:{has_twinkle}b,Trail:{has_trail}b,Colors:[I{colour}],FadeColors:[I{fade_colour}]}}]}}}} {cmd_count}', final_count

        # I cannot stress how annoyed i was to find out the minecraft changed the way you give items with nbt data a month ago
    
from .views import medal_types
def get_item_command(profile_controller):
    
    medals = medal_types(profile_controller.get_achievements_repo().achievements_for_whole_collection_since(min_datetime))
    username = local_conf["minecraft_username"]

    item_dict = {}

    # variables required to percist outside the loop
    commands = []
    medal_index = -1
    items_left = 0
    minecraft_id = "pufferfish" # should never be given, i just find them funny
    count = 0

    for m in medals:
        if(m.medal.minecraft_id not in item_dict):
            item_dict[m.medal.minecraft_id] = m.count
            continue

        item_dict[m.medal.minecraft_id] += m.count

    for item in item_dict:
    
        # Get the item
        if(items_left <= 0): # The old item has been completely added, a new item can now be added
            # Get the data for the item
            medal_index += 1
            minecraft_id = item.replace("minecraft:", "")
            count = item_dict[item]

            items_left = count

        # check for special item
        if(minecraft_id in SPECIAL_ITEMS):
            cmd, items_left = get_special_item_command(minecraft_id, items_left)
            commands.append(cmd)
            continue

        # Check if item count is larger than 6400 and if it is, record the amount of items left to generate a new command with
        count = min(count, 6400)
        items_left = items_left - count

        # If this is the first time for a new command
        commands.append(f"/give {username} {minecraft_id} {count}")

    return commands