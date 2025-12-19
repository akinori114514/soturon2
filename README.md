# 卒論作業ファイル構成

> 最終更新: 2025-12-19

## 📂 ディレクトリ構成

```
卒論作業ふぁいる/
├── README.md              ← このファイル（構成説明）
├── research_plan.md       ← 研究計画書
├── todo.md                ← 作業チェックリスト
├── CodeXlog.md            ← 作業ログ
├── ４軸分析.md            ← 4軸分析のメモ
│
├── chapters/              ← 章ごとの分割ファイル（★メイン作業対象）
│   ├── 00_intro.md        　　（はじめに）✅ 修正済み
│   ├── 01_china.md        　　（第1章：中国SCS）✅ 仮完成
│   ├── 02_chibis_score.md 　　（第2章：商務誠信/選択圧）🔧 追記中
│   ├── 03_japanscore.md   　　（第3章：日本）🔧 骨格＋注釈
│   ├── 04_EUUSAcompare.md 　　（第4章：米国・EU）🔧 骨格のみ
│   ├── 05_comperechijap.md　　（第5章：日中比較）🔧 骨格のみ
│   ├── 06_proposal.md     　　（第6章：提案）🔧 骨格のみ
│   └── 07_conclusion.md   　　（おわりに）⏳ 未着手
│
├── refs/                  ← 参考資料
│   ├── bassui.md          　　根拠カード集
│   ├── china_facts.md     　　中国SCSファクト整理
│   ├── references.md      　　参考文献リスト
│   └── *.pdf              　　元PDF資料
│
├── tools/                 ← スクリプト
│   └── ocr_refs.sh        　　OCRバッチ処理
│
└── _archive/              ← 旧版アーカイブ（削除せず保存）
    ├── _ocr/              　　OCR処理済みPDF（退避）
    ├── _text/             　　OCR抽出テキスト（退避）
    ├── keigosoturon_old_draft.md  ← 旧ドラフト（素材として保存）
    ├── full_draft_20241208.md
    ├── full_draft_20241208.docx
    ├── main_20241208.md
    └── 卒論仮統合（12-10ver）.md
```

## 📝 ファイル役割

| ファイル | 役割 | 状態 |
|----------|------|------|
| `chapters/00_intro.md` | はじめに：問題意識、RQ、分析枠組み | ✅ 修正済み |
| `chapters/01_china.md` | 第1章：中国SCS制度アーキテクチャ分析 | ✅ 仮完成 |
| `chapters/02_chibis_score.md` | 第2章：商務誠信（企業信用）と選択圧 | 🔧 追記中 |
| `chapters/03_japanscore.md` | 第3章：日本の信用情報インフラ | 🔧 骨格＋注釈 |
| `chapters/04_EUUSAcompare.md` | 第4章：米国・EU参照 | 🔧 骨格のみ |
| `chapters/05_comperechijap.md` | 第5章：日中比較 | 🔧 骨格のみ |
| `chapters/06_proposal.md` | 第6章：日本の提案モデル | 🔧 骨格のみ |
| `chapters/07_conclusion.md` | おわりに | ⏳ 未着手 |
| `refs/bassui.md` | 根拠カード（抜粋+日本語訳+4軸タグ） | - |
| `refs/china_facts.md` | 中国SCSの用語・ファクト整理 | - |

## 🎯 分析枠組み

**4軸（制度の骨格）**：
1. ガバナンス（意思決定主体）
2. データフロー（収集・連結・提供の経路）
3. インセンティブ設計（優遇・制裁・取引条件）
4. 官民関係（役割分担）

**中核メカニズム（どう効くか）**：
- 堀内（2019）の「逆適応」概念
- 本稿独自概念「ホワイトリスト型の選択圧」

## 🔄 作業フロー

1. `chapters/*.md` で各章を執筆・編集
2. `refs/bassui.md` / `refs/references.md` を参照し、必要に応じて `_archive/_text` を確認
3. 完成時に Word 出力

## 📋 次のタスク（優先度順）

1. **第2章（企業信用）の拡張**：章構成まで広げる
2. **第3章（日本）の出典補強**：CIC/JICC等の構造と論点の裏取り
3. **第4章（米EU）・第5章（日中比較）の本文拡充**
4. **第6章（提案）と結論の具体化**：脚注の精緻化と整合
