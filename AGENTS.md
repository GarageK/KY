# TouchDesignerLab 開発規約

## 1. 目的

このワークスペースでは、TouchDesignerを使った複数の実験・実装を、再利用可能なモジュールとして開発する。`LaserWave`はそのうちの1モジュールとして扱い、元の動作資産を保護する。

## 2. 役割定義

役割と権限の参照元は `C:\Work\OneWorks\agents\` とする。

- `secretary-pm`: 依頼整理、進行、成果統合、完了判定
- `architect`: 要件、境界、依存、安全策、構造設計
- `developer`: 実装、テスト、デバッグ、技術文書
- `reviewer`: 要件、正確性、安全性、変更影響の独立確認
- `researcher`: TouchDesigner、機器、SDK等の追加調査が必要な場合に使用

通常は、1つの作業を次の順序で進める。

`Secretary PM整理 → Architect設計 → Developer実装・検証 → Reviewer確認 → Secretary PM統合`

役割は工程上の責任分担を表す。別Agentへの委譲や並列作業は、Ownerが明示的に求めた場合、または適用される上位指示で許可された場合のみ行う。

## 3. プロジェクト構造

- `LaserWave/`: 既存レーザー制御資産と関連資料
- `TouchDesignerLab/`: 今後作成する統合プロジェクト
- `TouchDesignerLab/modules/`: 個別機能モジュール
- `TouchDesignerLab/shared/`: 共通スクリプト、設定、素材
- `TouchDesignerLab/docs/`: 設計、判断、運用手順
- `TouchDesignerLab/backups/`: 自動変更前のバックアップ
- `TouchDesignerLab/codex_bridge/`: 解析・自動編集ブリッジ

## 4. LaserWave保護方針

- `LaserWave/LaserWave.toe`を原本として扱い、直接上書きしない。
- 統合作業は複製または新規`TouchDesignerLab.toe`で行う。
- LaserWaveは`modules/LaserWave`として分離可能な構造へ移行する。
- 相対参照、絶対OPパス、外部ファイル、カメラIP、Helios番号を移行前に記録する。
- 変更前にスナップショットと復元可能なバックアップを作成する。

## 5. レーザー安全規則

- 自動解析と初期実装はレーザー出力を無効にして行う。
- `Brightness = 0`、`Test Mode = Off`を既定の安全状態とする。
- Helios / Laser Device CHOPを有効化する変更は、Ownerの明示指示なしに行わない。
- 出力有効化とモジュール有効化を別のインターロックにする。
- 実機テスト用変更には、緊急停止、投影範囲、反射面、人の立入りに関する確認事項を残す。

## 6. 変更とレビュー

- 既存ファイルの削除、履歴破壊、原本上書きは行わない。
- 自動編集命令は対象パスの許可リスト、Dry Run、操作ログ、ロールバック手段を備える。
- TouchDesigner内で未検証の変更は、検証済みと表現しない。
- 完了報告には、変更内容、検証結果、未検証事項、残存リスクを含める。

## 7. 解析量とコンテキスト管理

- 通常調査はGit差分、対象OP、対象パラメータ、直近の結果ログに限定する。
- 巨大な全ネットワークスナップショットは、初回ベースライン取得、構造不明時、重大な回帰調査に限る。
- 状態確認には、必要な値だけを返す小型のブリッジアクションを優先する。
- `.toe`変更の前後比較には、可能な範囲で`toeexpand`のテキスト差分を使用する。
- 画像取得は視覚確認が必要な最終候補に限定し、同一状態の重複キャプチャを避ける。
- 複数の読み取り・変更・検証は、安全性を損なわない範囲で一括実行する。
- 作業再開に必要な構造、判断、検証結果、未検証事項は`TouchDesignerLab/docs/`へ記録し、過去ログ全体の再読込を避ける。
- 詳細な運用基準は`TouchDesignerLab/docs/CONTEXT_EFFICIENCY.md`を参照する。
