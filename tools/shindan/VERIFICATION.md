# 実装・検証記録

## 作業開始点

- 本番のcanonical deployment、fetch後のorigin/main、同期後のローカルHEADはすべて `6ae7fce0f8494c0a7fea271c258192374cd7b8de`。
- Cloudflare本番deployment ID: `f81178de-89fa-4c8d-a2f1-696ca20c4eb6`。
- ブランチ: `feature/shindan`。既存運用のmainチェックアウトを切り替えず、別worktreeで作業。
- 配信ルートはリポジトリ直下だったため、ユーザーの追加承認に基づきPagesの出力先を `dist` に変更。
- build commandは `cloudflare-build.json` に記録。旧main相当のfixtureでも動作を確認。設定更新直後の本番deployment IDは不変。

## 実行結果

- Node 24.19: `node --test tools/shindan/core.test.mjs tools/shindan/quiz.test.mjs tools/shindan/result.test.mjs` — 14テスト成功。
- 全4096回答を独立した多数決の期待値と比較。16コードがそれぞれ256回出現。割合は67または100。
- 相性の全反転と二重反転、味8・食べ方4・手間2・冒険度1の順序、同点のデータ順、3品の重複なしを確認。
- 通常は800ms待機、reduced-motionは待機なし、回答の選び直し、履歴復帰、読み込み失敗を確認。
- `python tools/shindan/check.py` — 18ページのメタと静的内容、内部リンク、17 PNGの1200×630、16種のキャラクターと解説を確認。
- `python tools/shindan/check.py --dist` — 公開ファイルのバイト一致、tools・Python・フォントの除外を確認。
- `python tools/shindan/test_package.py` — 既存main相当の梱包テスト成功。
- 再生成前後の18 HTML・17 PNGのSHA256が全一致（再現性を確認）。
- `git apply --check tools/shindan/integration-proposal.diff` — 差分案が適用可能であることだけを確認。適用はしていない。

## ブラウザー

- 360×640のiframe、ライト／ダーク双方の実際のmedia queryで132パターン成功。
- トップ・一覧・全16結果×ハッシュなし／有効2種類／不正を確認。横スクロールなし。
- 全16結果の一言までの下端は最大401px。キャラクター・コード・名前・一言が640px以内に収まる。
- 各ページのキャラクター画像読み込み、対応コード、特徴・理由・楽しみ方の表示を確認。
- 4軸の説明がコードの各文字に一致。67%なら3問中2問、100%なら3問中3問の説明になることを全タイプで確認。
- 同じページ内で有効ハッシュを不正ハッシュに変更すると、割合・回答数・個人向け見出しが消えることも確認。
- 設問ボタンの実測高さ80px。開始、前へ戻る、回答変更、12問回答、結果への遷移を確認。
- Q1を選び直した実操作で `/shindan/result/kgra/#p=67-67-67-67` に遷移。
- キーボードの本文スキップで割合のハッシュが消えないこと、リンクコピーの成功表示を確認。
- 本番LPのDOMでCloudflare Web Analyticsの自動挿入を確認。既存設定を維持し、HTMLで二重追加しない。

## キャラクターと詳細解説

- 内蔵image_genで16点を別々に生成。SCROを画風の参照として使用し、PNGのアルファを保ったまま512×512のWebPへ出力。
- 配信する16画像は合計801,892 bytes、最大58,098 bytes。すべて異なる画像であることと透過を確認。
- 最終画像は `shindan/assets/characters/`、プロンプト一式は `tools/shindan/character-prompts.json` に保存。
- 16ページのタイプ紹介・判定理由・各軸の説明・今夜の楽しみ方はJSONから静的生成。個々の設問で何を選んだかは推測しない。
- 結果用16 OGPにも対応キャラクターを使用。名前が長いSGROの画像を目視確認し、全17 PNGの寸法チェックと再生成時のバイト一致も成功。

## Cloudflareプレビュー

- URL: https://feature-shindan.banshaku-lp-site.pages.dev/shindan/
- 初回のGit連携ビルド・デプロイが成功。公開18ページでHTTP 200と必須メタ、既存LPと同一の計測タグが1個だけ挿入されることを確認。
- 全17 PNGはHTTP 200、1200×630、リポジトリ内の画像とバイト一致。
- build.py、core.test.mjs、NotoSansJP.ttf、README.mdの公開URLはすべて404。toolsは配信されない。
- 既存トップページはHTTP 200。
- 最終コミットのCloudflareチェック結果はPRのChecksから確認できる。

## 共有URLの修正

- 2026-09-28に本番の `/shindan/result/kcto/` と `/shindan/` が404、同じパスのブランチプレビューが200であることを確認。PRは未マージ。
- 原因はブラウザーの共有先に本番固定のcanonicalを使っていたこと。閲覧中のページURLからクエリとハッシュを除いたURLへ修正。
- 全16タイプ×本番・ブランチプレビュー・固有デプロイURLで、X・Threads・コピー・OS共有の送信内容が同じ公開環境を指すことをNodeで検証。
- クリップボードが使えない場合の手動コピー欄も、閲覧中のURLを維持することを確認。
- 360px・ライト／ダークの132パターンを再実行し、X・Threadsの共有先ホスト一致とクエリ／ハッシュ除外も成功。
- 本番固定のcanonicalとOGPメタは維持。本番URLそのものの有効化は、当初の「マージしない」指定を変更して本番公開する段階で行う。

## 制限・未実施

- X・Threadsへの実投稿はしていない。SNS側のOGPキャッシュ反映とOSの共有先アプリは未検証。
- 全16レシピのURLは指定どおり空。名前のみを表示する。
- Threadsプロフィールは未指定のため定数を空にして非表示。
- LPトップへのリンクとsitemapは未適用の差分案のみ。
- mainへ直接コミット・pushせず、PRもマージしない。本番の診断ページ公開はマージ後。
