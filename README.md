# 卒論作業ファイル構成

> 最終更新: 2024-12-08

## 📂 ディレクトリ構成

```
卒論作業ふぁいる/
├── README.md              ← このファイル（構成説明）
├── keigosoturon.md        ← ★正本：詳細プロット+ドラフト
├── research_plan.md       ← 研究計画書
├── todo.md                ← 作業チェックリスト
├── CodeXlog.md            ← 作業ログ
│
├── chapters/              ← 章ごとの分割ファイル
│   ├── intro.md           　　（はじめに）
│   ├── china.md           　　（第1章：中国SCS）
│   ├── japan.md           　　（第2章：日本）
│   ├── compare.md         　　（第3章：米国・EU比較）
│   ├── proposal.md        　　（第5章：提案）
│   └── conclusion.md      　　（おわりに）
│
├── refs/                  ← 参考資料
│   ├── bassui.md          　　根拠カード集
│   ├── china_facts.md     　　中国SCSファクト整理
│   ├── references.md      　　参考文献リスト
│   ├── _text/             　　OCR抽出テキスト
│   ├── _ocr/              　　OCR処理済みPDF
│   └── *.pdf              　　元PDF資料
│
├── tools/                 ← スクリプト
│   └── ocr_refs.sh        　　OCRバッチ処理
│
└── _archive/              ← 旧版アーカイブ（削除せず保存）
    ├── full_draft_20241208.md
    ├── full_draft_20241208.docx
    └── main_20241208.md
```

## 📝 ファイル役割

| ファイル | 役割 |
|----------|------|
| `keigosoturon.md` | **正本**：全章のドラフト。ここを編集してWord出力 |
| `chapters/*.md` | 章別の作業ファイル（注釈・脚注付与用） |
| `refs/bassui.md` | 根拠カード（抜粋+日本語訳+4軸タグ） |
| `refs/china_facts.md` | 中国SCSの用語・ファクト整理 |
| `todo.md` | 残タスク管理 |
| `research_plan.md` | 8週ロードマップ |

## 🔄 作業フロー

1. `todo.md` で作業項目を確認
2. `chapters/*.md` で注釈・脚注を追加
3. `refs/bassui.md` から根拠を引用
4. `keigosoturon.md` に統合・清書
5. 完成時に Word 出力
