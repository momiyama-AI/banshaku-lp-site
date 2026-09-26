# 晩酌つまみ16タイプ診断

配信するのはリポジトリ直下の `shindan/` 内の HTML・CSS・ES Module・JSON・PNG・WebP。
`tools/shindan/` は生成・検証用で、Cloudflare Pages の出力 `dist/` には含めません。
HTMLとOGPは生成物です。内容を変更するときはJSONと生成処理を編集して再生成してください。

## データとレシピの追加

- `shindan/data/types.json`: 軸の解説・グループ色・16タイプの名前と一言、キャラクター参照、特徴・判定理由・楽しみ方。
- `shindan/data/questions.json`: 表示順どおりの12問。各軸3問、各問2択。選択肢の順序は固定。
- `shindan/data/recipes.json`: レシピの配列。追加するときは次の形式を末尾へ追加します。

~~~json
{"name":"レシピ名","tags":"SCRO","url":"https://投稿のURL"}
~~~

`name` は重複させず、`tags` は味(S/K)・食べ方(C/G)・手間(R/T)・冒険度(O/A)の4文字。
URLが未定なら空文字のままで構いません。URLにはHTTPSの公開レシピ／投稿URLを使います。
タグが一致する軸の点数（8・4・2・1）の合計で3品を選びます。同点時はJSONで上にあるレシピを優先します。
データ更新後は、静的な代替表示も更新するため再生成し、JSONと生成物を一緒にコミットしてください。

## 結果のキャラクターと解説

全16タイプに別々のキャラクターを用意し、`shindan/assets/characters/{code}.webp` に保存しています。
内蔵 `image_gen` で生成したイラストを、透過を維持して512×512に縮小・WebP化しました。
生成プロンプト一式は `character-prompts.json`。SCROを画風の参照として、各タイプの料理・服装・表情を描き分けています。
生成にはCLI/APIキーモードを使用していません。通常のページ再生成に画像生成サービスは不要です。

タイプごとの `character.src` と `character.alt` が画像と代替テキスト、`description` が特徴、
`reason` が4軸の組み合わせの説明、`tip` が今夜の楽しみ方です。
各軸の `explanations` は `letters` / `labels` と同じ順で2件を記載してください。
解説と画像は静的HTMLにも埋め込まれ、JavaScriptなし・割合なしでも閲覧できます。
結果用OGPにも対応するキャラクターを合成します。

有効な割合ハッシュがある場合だけ、「3問中2問／3問がどちら側だったか」を解説に追加します。
URLには個々の回答を持たないため、「Q1でレモンを選んだから」など特定の選択肢を推測した文章は表示しません。
割合がない・不正・途中で消えた場合は、本人への判定理由を消してタイプ共通の解説に戻します。

## 再生成

リポジトリ直下で実行します。Python 3.10以上、Pillow、Node.js 22.7以上が必要です。
今回の検証環境は Python 3.12、Pillow 12.3、Node.js 24.19です。

~~~sh
python -m pip install Pillow
python tools/shindan/build.py
python tools/shindan/check.py
node --test tools/shindan/core.test.mjs tools/shindan/quiz.test.mjs
python tools/shindan/test_package.py
~~~

`build.py` の `BASE_URL` が本番URLの唯一の定義です。canonical・OGP・共有URLはここから生成されます。
プレビューでもcanonicalと共有先は本番URLです。マージ前は本番の `/shindan/` がまだ公開されていない点に注意してください。

Noto Sans JPは `tools/shindan/fonts/NotoSansJP.ttf` に同梱しています。フォントを復元する場合:

~~~sh
python tools/shindan/download_font.py
~~~

取得元は[Google Fonts](https://github.com/google/fonts/tree/66a36c8c94b1a5d992ee4e7f392fccfe4945767c/ofl/notosansjp)の固定リビジョンです。
ライセンスは `fonts/OFL.txt`。フォントSHA256:
`c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f`

フォントを取得できない環境では、配信済みPNGを保持して `python tools/shindan/build.py --skip-images` でHTMLだけを更新できます。
これは画像の再生成完了を意味しません。変更したタイプ名・一言を画像へ反映できなかった場合は必ず報告してください。

## 公開用フォルダーとプレビュー

初回のローカル作業では未追跡ファイルを含めて梱包します。

~~~sh
python tools/shindan/package_site.py --include-untracked
python tools/shindan/check.py --dist
python -m http.server 8767 --bind 127.0.0.1 --directory dist
~~~

`http://127.0.0.1:8767/shindan/` で診断できます。
`dist/` が既にある場合、スクリプトは古い生成物を混ぜないため停止します。自分で生成したリポジトリ直下の `dist/` だけを削除して再実行してください。
`dist/.gitignore` はパッケージ処理が作るローカル専用ファイルです。既存の `.gitignore` は変更しません。

Cloudflare Pages はビルドコマンドを以下のコマンドで表示される文字列に、出力先を `dist` に設定します。

~~~sh
python tools/shindan/package_site.py --print-build-command
~~~

このコマンドはGit追跡済みの公開ファイルをコピーするPython標準ライブラリだけの処理です。
`tools/`、`dist/`、`node_modules/`、`functions/`、`.well-known` を除く隠しファイルを除外します。
新しいスクリプトがまだ存在しないmainでも動作するため、PR未マージ中の既存投稿・画像のデプロイを妨げません。
CIでPillowやフォントを取得する必要はありません。事前生成したHTML・PNGをそのまま配信します。
本機能はPages FunctionsやWorkerを追加しません。

## 検証範囲

- `core.test.mjs`: 全4096通りを独立した多数決の期待値と比較、16コード各256回、割合67/100、反転、3品の重複なし、軸の重み、同点順、入力異常、ハッシュ、共有URL。
- `quiz.test.mjs`: 通常の800ms待機、reduced-motion時の即時遷移、回答変更、戻る操作、データ取得失敗、ブラウザーの履歴復帰。
- `check.py`: 18ページの必須メタ、絶対OGP URL、17枚のPNG寸法、16種の透過キャラクター画像と対応・寸法・サイズ、静的な特徴と4軸の説明・相性・おすすめ、内部リンク、外部コード不使用。
- `check.py --dist`: 上記に加え、ツール・Python・フォントの混入防止と元ファイルとのバイト一致。
- `test_package.py`: 新規スクリプトのないmain相当のfixtureで、公開ファイルの保持とツール除外。

ブラウザーの360px表示を再確認するには、リポジトリ直下をローカルで配信し、
`/tools/shindan/browser-check.html` を開いて「全ページの幅・結果表示を検証」を押します。
テスト専用iframeを360×640にし、iframeの `color-scheme` から実際の `prefers-color-scheme` を切り替えます。
トップと一覧、全16結果×ハッシュなし・2種類の正しいハッシュ・不正ハッシュをライト／ダークで検証（132パターン）。
キャラクターの読み込みと対応、4軸それぞれの回答数・ラベル、ハッシュ変更時に古い個人向け説明が残らないことも確認します。
本番用distにはこの検証ページを含めません。

手動では開始→12問→結果、前の質問へ→選び直し、コピー、一覧・相性リンク、縦スクロールも確認してください。
X/Threadsのリンク先への実投稿、OSの共有先アプリの動作、各SNSクローラーのOGP反映は自動テストには含みません。

## 計測・個人情報・フォロー

回答の送信、Cookie、LocalStorage、SessionStorage、外部ライブラリ、Webフォント/CDNは使いません。
結果の割合は `#p=67-100-67-100` というハッシュにだけ入れ、共有時には除きます。
HTMLソースに解析タグはありませんが、Cloudflare PagesのWeb Analytics自動挿入が有効です。
既存の自動挿入設定を保持し、配信時に全ページへ同じ計測タグを追加します。生成HTMLへの二重追加はしません。
参考: https://developers.cloudflare.com/pages/how-to/web-analytics/
LPのAdSense広告タグは解析タグではなく、Cookie不使用の条件に合わせて診断には追加していません。
`shindan/assets/result.js` の `THREADS_PROFILE_URL` は空です。公式URLが確認できたら設定してください。空の間は非表示です。

## 変更の境界

既存HTML・sitemap・ビルド用ファイルを編集せず、`shindan/` と `tools/shindan/` の追加だけで実装しています。
Cloudflare側のビルド設定変更は別途ユーザー承認済みです。
LPトップのリンクとsitemapは `integration-proposal.diff` に差分案だけを保存しています。適用していません。
追加ファイルの全一覧は `FILES.txt`、実行した確認結果は `VERIFICATION.md` を参照してください。
