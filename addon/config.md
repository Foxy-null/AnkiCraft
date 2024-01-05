## AnkiCraft: Configuration (English)

`language` and `OnlyShowTooltip` may works properly.

These settings do not sync and require a restart to apply.
TODO: SOME CONFIGS NOT FUNCITONAL YET, PLACEHOLDER ONLY

- `language` [`en`, `ja`]: `en` for English, `ja` for Japanese.
- `WhereToShowMedals` [`all`, `oldstat`, `disabled`]: Where to show your all obtained items. (You can still get items even if you set it to `disabled`.)
- `FontRange` [`disabled`, `overview`, `all`]: Where to apply Minecraft font. 
- `show_image_on_tooltip` [`true`, `false`]: Whether to display the image on the Tooltip that appears when answering the card. 
- `duration` [int]: duration to show medals in msec; default: `1500`
- `tooltip_color` [string]: HTML color code; default: `#AFFFC5` (light green)
- `multikill_interval_s` [int]: Time between card answers to count for multikill
- `killing_spree_interval_s` [int]: Time between card answers to count for killing spree

## AnkiCraft: 各種設定（日本語）

こちらの項目では私が独自に追加した幾つかの設定をご紹介します。元のKillStreaksアドオンの設定の動作は未確認です。

- `language` [`en`, `ja`]: `en` = 英語、`ja` = 日本語
- `WhereToShowMedals` [`all`, `oldstat`, `disabled`]: 獲得したアイテム一覧をどこに表示するかの設定。（`disabled`に設定しても引き続きアイテムはカウントされます）
- `FontRange` [`disabled`, `overview`, `all`]: Minecraftのフォントを適用する場所の範囲。 
  （日本語については[美咲フォント](https://littlelimit.net/misaki.htm)を使用しています。）
- `show_image_on_tooltip`: 回答時に表示されるツールチップ上に画像を表示するかどうかの設定。