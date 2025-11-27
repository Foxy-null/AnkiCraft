# [AnkiCraft](https://ankiweb.net/shared/info/368161874)
[![Addon Download](https://github-production-user-asset-6210df.s3.amazonaws.com/72304646/263796774-b60e19fa-60b3-456e-9d82-a261fe0af1b8.png)](https://ankiweb.net/shared/info/368161874)
## DEMO

https://github.com/Foxy-null/AnkiCraft/assets/72304646/9066b4c9-93e5-4490-a10a-ff9f852f27a5

<details>
<summary>More Screenshots</summary>
<img src="https://github.com/Foxy-null/AnkiCraft/assets/72304646/ac31a2c4-ff8b-46ed-b736-7b12bea6aea6">
<img src="https://github.com/AnKing-VIP/anki-audiovisual-feedback/assets/72304646/b8a7736e-d896-45b7-92a5-5c46f1ef0ac7">
</details>

*Achievements screen requires [Audiovisual Feedback](https://ankiweb.net/shared/info/231569866) addon and [AnkiCraft theme](https://github.com/AnKing-VIP/anki-audiovisual-feedback/wiki/Minecraft)

## Change from the original Killstreaks addon
 
 - Removed Chase mode from menu
 - Fixed [this Issue](https://github.com/jac241/anki_killstreaks/issues/46) of Killstreaks addon
 - Added "All unclaimed items" field instead of "Today's all medals" and "All medals from This deck" fields.
 - Your unclaimed Items syncs between computers now!
 - Added Claim items in Minecraft feature. (Thanks to [Kyron](https://github.com/AvianSamurai)!)
 - ...and some more bits (I don't remember haha)

## Requirements
 - [This addon](https://ankiweb.net/shared/info/368161874)
 - [Audiovisual Feedback](https://ankiweb.net/shared/info/231569866)
 - [AnkiCraft SFX](https://github.com/Foxy-null/AnkiCraft/raw/main/AnkiCraft.zip)

## Installation

> [!Caution]  
> Users of the "Contanki" add-on will need to change their controller settings, see the "For Contanki Users" section below.

1. Thumbs up to this add-on in AnkiWeb page if you like it :)
    - (Also star to GitHub repository too! Greatly appreciate you!) 

2. Install [AnkiCraft](https://ankiweb.net/shared/info/368161874) from AnkiWeb and choose one option.

3. Install [Audiovisual Feedback](https://ankiweb.net/shared/info/231569866).

4. add `AnkiCraft` folder in theme folder.
  (It'll be `%appdata%\Anki2\addons21\231569866\user_files\themes\AnkiCraft\images`)

<details>
<summary><h2>日本語</h2></summary>
1. （このアドオンを気に入ってくださったら）高評価をする。
    - (GitHubのリポジトリにもStarして頂くと泣くほど嬉しいです！)

2. AnkiWebから[AnkiCraft](https://ankiweb.net/shared/info/368161874)をインストールする。

3. アドオンのコンフィグから"language"の値を"ja"に変更

4. [Audiovisual Feedback](https://ankiweb.net/shared/info/231569866)をインストールする。

5. `AnkiCraft`フォルダーをテーマフォルダー内に置く。
  （こんな感じになるはず→`%appdata%\Anki2\addons21\231569866\user_files\themes\AnkiCraft\images...`）

</details>

> [!Caution]
> "Contanki"アドオンを使用されている方は、ご自身のコントローラー設定を変更して頂く必要があります。詳細は "For Contanki Users"セクションをご確認ください。

## For Contanki Users

1. Open Contanki settings
2. Register all answer keys as "Custom Action"

Ex:
| Custom Action | Shortcut |
| ------------- |:--------:|
| Againkey      | 1        |
| Goodkey       | Space    |
| Hardkey       | 3        |
| Easykey       | 4        |

3. Replace all "Flip Card" actions with "Goodkeys" in the `"Controller" > "Question"` tab
4. Replace all "`(Answer)`" actions with "`(Answer)`key" in the `"Controller" > "Answer"` tab

<details>
<summary><h2>日本語</h2></summary>

1. Contankiの設定を開く
2. Ankiの回答キー全てを"Custom Action"として割り当てる

例：
| Custom Action | Shortcut |
| ------------- |:--------:|
| Againkey      | 1        |
| Goodkey       | Space    |
| Hardkey       | 3        |
| Easykey       | 4        |

3. `"Controller" > "Question"`タブに存在する全ての"Flip Card"アクションを"Goodkeys"に置き換える
4. `"Controller" > "Answer"`タブに存在する全ての"`(回答キー名)`"を"`(回答キー名)keys`"に置き換える

</details>

## Usage

1. Select biome to explore
2. Collect some items
3. Claim items by clicking AnkiCraft > Claim Items and pasting in each spawn command to your Minecraft world
4. Click reset when prompted to clear the claimed items from Anki
 
## Note
 
 - This is a customized version of [Anki Killstreaks](https://ankiweb.net/shared/info/579111794) addon by [jac241](https://github.com/jac241).
    So, Almost all issues of Killstreaks addon is not fixed yet.
 - I have only poor skill for both of English and Coding.
 - This is my first work on GitHub
 - old repository was deleted for cleaning up my Git LFS Storage, sorry...
 - Generally, the number of items you can earn is fixed based on the number of correct combos of Anki cards. When you reach the highest combo of items you can earn, your item rank is reset. However, some biomes are set up with multiple layers, and each layer has a different number of combos for which the ranks are reset, allowing for more complex combinations of items to be awarded.

## Special Thanks

### [jac241](https://github.com/jac241) - The creator of the wonderful Killstreaks add-on

### [Kyron](https://github.com/AvianSamurai) - A great contributor to the creation of the item claiming function!

### [Shigeyuki](https://www.patreon.com/Shigeyuki) - Anki's 23.10+ version support would not have been possible without his contributions.

## Reporting issues

Please report issues through Github. Include a description of what you were doing, the error message shown in Anki, and a screenshot if possible.

Also, report in Japanese or English.

...Leaving aside my ability to fix those issues.


## Author
 
 - Foxy_null
 - Twitter: [@Foxy_null](https://twitter.com/foxy_null)
 - Email: foxynull@duck.com
 - Discord: @foxy_null
 
## License and Credits
 
    "AnkiCraft" is under [GNU AGPLv3](https://www.gnu.org/licenses/agpl.html).

    Modifications by jac241 <https://github.com/jac241> for Anki Killstreaks addon
    Customized by Foxy_null <https://github.com/Foxy-null> for AnkiCraft addon ^^

    AnkiCraft is totally free and open-source software.

## Support this add-on

Your [rating](https://ankiweb.net/shared/review/368161874) and star to GitHub repository will help us develop the add-on! Thank you!!!

## Star History

<a href="https://star-history.com/#Foxy-null/AnkiCraft&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Foxy-null/AnkiCraft&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Foxy-null/AnkiCraft&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Foxy-null/AnkiCraft&type=Date" />
 </picture>
</a>
