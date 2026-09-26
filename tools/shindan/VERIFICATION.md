# 実装・検証記録

## 作業開始点

- 本番のcanonical deployment、fetch後のorigin/main、同期後のローカルHEADはすべて `6ae7fce0f8494c0a7fea271c258192374cd7b8de`。
- Cloudflare本番deployment ID: `f81178de-89fa-4c8d-a2f1-696ca20c4eb6`。
- ブランチ: `feature/shindan`。既存運用のmainチェックアウトを切り替えず、別worktreeで作業。
- 配信ルートはリポジトリ直下だったため、ユーザーの追加承認に基づきPagesの出力先を `dist` に変更。
- build commandは `cloudflare-build.json` に記録。旧main相当のfixtureでも動作を確認。設定更新直後の本番deployment IDは不変。

## 実行結果

- Node 24.19: `node --test tools/shindan/core.test.mjs tools/shindan/quiz.test.mjs` — 12テスト成功。
- 全4096回答を独立した多数決の期待値と比較。16コードがそれぞれ256回出現。割合は67または100。
- 相性の全反転と二重反転、味8・食べ方4・手間2・冒険度1の順序、同点のデータ順、3品の重複なしを確認。
- 通常は800ms待機、reduced-motionは待機なし、回答の選び直し、履歴復帰、読み込み失敗を確認。
- `python tools/shindan/check.py` — 18ページのメタと静的内容、内部リンク、17 PNGの1200×630を確認。
- `python tools/shindan/check.py --dist` — 公開ファイルのバイト一致、tools・Python・フォントの除外を確認。
- `python tools/shindan/test_package.py` — 既存main相当の梱包テスト成功。
- 再生成前後の18 HTML・17 PNGのSHA256が全一致（再現性を確認）。
- `git apply --check tools/shindan/integration-proposal.diff` — 差分案が適用可能であることだけを確認。適用はしていない。

## ブラウザー

- 360×640のiframe、ライト／ダーク双方の実際のmedia queryで100パターン成功。
- トップ・一覧・全16結果×ハッシュなし／有効／不正を確認。横スクロールなし。
- 全16結果の一言までの下端は最大322px。コード・名前・一言が640px以内に収まる。
- 設問ボタンの実測高さ80px。開始、前へ戻る、回答変更、12問回答、結果への遷移を確認。
- Q1を選び直した実操作で `/shindan/result/kgra/#p=67-67-67-67` に遷移。
- キーボードの本文スキップで割合のハッシュが消えないこと、リンクコピーの成功表示を確認。
- 本番LPのDOMでCloudflare Web Analyticsの自動挿入を確認。既存設定を維持し、HTMLで二重追加しない。

## 制限・未実施

- X・Threadsへの実投稿はしていない。SNS側のOGPキャッシュ反映とOSの共有先アプリは未検証。
- 全16レシピのURLは指定どおり空。名前のみを表示する。
- Threadsプロフィールは未指定のため定数を空にして非表示。
- LPトップへのリンクとsitemapは未適用の差分案のみ。
- mainへ直接コミット・pushせず、PRもマージしない。本番の診断ページ公開はマージ後。
