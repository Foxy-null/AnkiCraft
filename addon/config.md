## AnkiCraft: Configuration (English)

`language` and `OnlyShowTooltip` may works properly.

These settings do not sync and require a restart to apply.
TODO: SOME CONFIGS NOT FUNCITONAL YET, PLACEHOLDER ONLY

- `language` [string]: `en` for English, `ja` for Japanese.
- `OnlyShowTooltip` [boolean]: Whether to hide the overview of all items from the menu. (Items will continue to be counted even if set to `true`.)
- `FontRange` [string]: where to apply Minecraft font. (`disabled`, `overview`, `all`) 
- `duration` [int]: duration to show medals in msec; default: `1500`
- `tooltip_color` [string]: HTML color code; default: `#AFFFC5` (light green)
- `multikill_interval_s` [int]: Time between card answers to count for multikill
- `killing_spree_interval_s` [int]: Time between card answers to count for killing spree

## AnkiCraft: 各種設定（日本語）

こちらの項目では私が独自に追加した２つの設定をご紹介します。元のKillStreaksアドオンの設定の動作は未確認です。

- `language` [string]: `en` = 英語、`ja` = 日本語
- `OnlyShowTooltip` [boolean]: すべての画面からアイテム一覧を隠すかどうかの設定（`true`でもアイテムはカウントされます）
- `FontRange` [string]: Minecraftのフォントを適用する場所の範囲 (`disabled`, `overview`, `all`) 
  （日本語については[美咲フォント](https://littlelimit.net/misaki.htm)を使用しています。）