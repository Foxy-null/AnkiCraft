## AnkiCraft: Configuration (English)

`language` and `OnlyShowTooltip` may works properly.

These settings do not sync and require a restart to apply.
TODO: SOME CONFIGS NOT FUNCITONAL YET, PLACEHOLDER ONLY

- `language` [`en`, `ja`]: `en` for English, `ja` for Japanese.
- `WhereToShowMedals` [`all`, `oldstat`, `disabled`]: Where to show your all obtained items. (You can still get items even if you set it to `disabled`.)
- `FontRange` [`disabled`, `overview`, `all`]: Where to apply Minecraft font.
- `show_image_on_tooltip` [`true`, `false`]: Whether to display the image on the Tooltip that appears when answering the card.
- `duration` [int]: duration to show medals in msec; default: `1500`
- `tooltip_color` [`string`]: HTML color code; default: `#AFFFC5` (light green)
- `multikill_interval_s` [int]: Time between card answers to count for multikill
- `killing_spree_interval_s` [int]: Time between card answers to count for killing spree
- `play_sound` [`true`, `false`]: Whether to play sound effects upon obtaining items.
  - (Ensure that the "Play feedback during review" option in the "AudioVisual Feedback" add-on settings and the "Advanced Answer Sound" add-on are both disabled.)
- `minecraft_version_is_pre_1_20_5` [`true`, `false`]: (Only for Java users) Corresponds to the system changes Mojang made in Minecraft 1.20.5.
- `is_bedrock_edition` [`true`, `false`]: Whether to use Bedrock Edition command formats when generating command text.
- `minecraft_username` [`string`]: Enter the username or target selector to use when generating command text.
  - Tip: For users who have spaces in your xbox gamertags, you can use double quotes with a backslash by placing it before the double quote.
  - Example: `\"Foxy null\"`

## AnkiCraft: 各種設定（日本語）

この設定は端末間で同期されません。変更を適用するには Anki を再起動してください。
元の KillStreaks アドオンの設定の動作は未確認です。

- `language` [`en`, `ja`]: `en` = 英語、`ja` = 日本語
- `WhereToShowMedals` [`all`, `oldstat`, `disabled`]: 獲得したアイテム一覧をどこに表示するかの設定。（`disabled`に設定しても引き続きアイテムはカウントされます）
- `FontRange` [`disabled`, `overview`, `all`]: Minecraft のフォントを適用する場所の範囲。
  （日本語については[美咲フォント](https://littlelimit.net/misaki.htm)を使用しています。）
- `show_image_on_tooltip`: 回答時に表示されるツールチップ上に画像を表示するかどうかの設定。
- `play_sound`: アイテム獲得時に効果音を鳴らすかどうかの設定。
- `minecraft_version_is_pre_1_20_5` [`true`, `false`]: （Java 版プレイヤー用の設定）Mojang が Minecraft バージョン 1.20.5 で加えたシステム変更へのパッチを有効化するか。
- `is_bedrock_edition` [`true`, `false`]: アイテム回収用のコマンドを生成するときに統合版用のコマンドフォーマットを使用するかどうか。
- `minecraft_username` [`string`]: コマンド生成時に使用する際に使用するユーザー名またはターゲットセレクターの設定。
  - ヒント: Xbox のゲーマータグにスペースが入っている方は、ダブルクオートの前にバックスラッシュ記号を置くことで正常にゲーマータグを記載することができます。
  - 例: `\"Foxy null\"`
