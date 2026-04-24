# LBD分析 再現手順（ナレッジグラフ作成まで）

## 1. 目的

本ドキュメントは、このリポジトリで実施したLBD（Literature-Based Discovery）分析のうち、  
**PDF文献の前処理から知識グラフ生成（`knowledge_graph.json`）まで**を再現するための手順書である。

対象範囲（Phase 1-4）:

1. PDF -> テキスト抽出
2. テキスト -> チャンク分割
3. チャンク -> 概念抽出（`concepts.json` 作成）
4. 概念DB統合 -> 知識グラフ生成

---

## 2. 再現モード

### モードA（推奨・最短）

既存の `lbd-pipeline/concepts/**/concepts.json` をそのまま使って再生成する。  
この場合、実行はPhase 1/2の確認 + Phase 4（`03` と `04`）が中心になる。

### モードB（フル再抽出）

`refs/*.pdf` からPhase 3の概念抽出まで再実行する。  
現状、Phase 3は専用自動スクリプトがないため、LLMを使った運用手順（本書6章）で再現する。

---

## 3. 前提環境

- 実行ディレクトリ: リポジトリルート
- 必須:
  - `bash`
  - `python3`（3.9以上推奨）
  - `pdftotext`（poppler）
- 任意（検証用）:
  - `jq`

`pdftotext` 未導入時（macOS）:

```bash
brew install poppler
```

---

## 4. 入出力対応（Phase 1-4）

| Phase | スクリプト | 入力 | 出力 |
|---|---|---|---|
| 1 | `lbd-pipeline/scripts/01_extract_text.sh` | `refs/*.pdf` | `lbd-pipeline/extracted/*.txt` |
| 2 | `lbd-pipeline/scripts/02_chunk_texts.py` | `lbd-pipeline/extracted/*.txt` | `lbd-pipeline/chunks/**/chunk_*.json` |
| 3 | （運用手順） | `lbd-pipeline/chunks/**/chunk_*.json` | `lbd-pipeline/concepts/**/concepts.json` |
| 4-1 | `lbd-pipeline/scripts/03_merge_concepts.py` | `lbd-pipeline/concepts/**/concepts.json` | `lbd-output/scs_concepts_db.json` |
| 4-2 | `lbd-pipeline/scripts/04_build_knowledge_graph.py` | `lbd-output/scs_concepts_db.json` | `lbd-output/knowledge_graph.json`, `lbd-output/gap_candidates.json` |

---

## 5. 実行手順（コマンド）

### 5.1 事前確認

```bash
cd "/Users/keigo/Documents/卒論作業ふぁいる　ローカル"
python3 --version
command -v pdftotext
```

### 5.2 Phase 1: PDF -> テキスト

```bash
bash lbd-pipeline/scripts/01_extract_text.sh
```

確認:

```bash
find refs -maxdepth 1 -name '*.pdf' | wc -l
find lbd-pipeline/extracted -maxdepth 1 -name '*.txt' | wc -l
```

### 5.3 Phase 2: テキスト -> チャンク

```bash
python3 lbd-pipeline/scripts/02_chunk_texts.py
```

確認:

```bash
jq '.total_sources, .total_chunks, .total_chars' lbd-pipeline/chunks/chunk_stats.json
```

### 5.4 Phase 3: チャンク -> 概念抽出（モードBのみ）

モードA（既存concepts利用）の場合はスキップしてよい。

Phase 3の最小要件:

- `lbd-pipeline/concepts/<source_id>/concepts.json` を作成する
- 各ファイルに `concepts` 配列を含める
- 各概念は最低限 `en_name` または `jp_name` を持つ

推奨スキーマ（下流処理で使われる項目を明示）:

```json
{
  "source_id": "Planning_Outline_for_the_Construction_of_a_Social_Credit_System_2014-2020",
  "extraction_date": "2026-02-12",
  "concepts": [
    {
      "jp_name": "連合懲戒",
      "en_name": "Joint Punishment",
      "zh_name": "联合惩戒",
      "concept_type": "mechanism",
      "definition": "定義テキスト",
      "four_axis": ["インセンティブ設計", "ガバナンス"],
      "source_papers": ["<source_id>"],
      "context_quotes": ["根拠引用"]
    }
  ],
  "relationships": []
}
```

抽出時の推奨設定（再現性確保）:

- モデル名を固定する
- `temperature=0`
- プロンプトを固定する
- チャンク順序（`chunk_0000` から昇順）を固定する

カバレッジ確認（chunksに対してconceptsが不足していないか）:

```bash
for d in lbd-pipeline/chunks/*; do
  [ -d "$d" ] || continue
  sid="$(basename "$d")"
  [ -f "lbd-pipeline/concepts/$sid/concepts.json" ] || echo "$sid"
done
```

### 5.5 Phase 4: 概念DB統合 -> KG生成

```bash
python3 lbd-pipeline/scripts/03_merge_concepts.py
python3 lbd-pipeline/scripts/04_build_knowledge_graph.py
```

確認:

```bash
jq '.concepts | length' lbd-output/scs_concepts_db.json
jq '.metadata.node_count, .metadata.edge_count' lbd-output/knowledge_graph.json
jq '.metadata.total_gaps' lbd-output/gap_candidates.json
```

---

## 6. Phase 3（概念抽出）の運用手順

1. `chunk_*.json` から `text` を取得する  
2. LLMに「SCS関連概念抽出」プロンプトを与える  
3. 抽出結果を source単位で `concepts.json` に統合して保存する  
4. JSON妥当性チェック後、Phase 4へ進む

推奨プロンプト骨子:

- 抽出対象: SCS制度、比較制度（JP/EU/US）、4軸に紐づく概念
- 除外対象: 汎用語のみの語、文脈依存で意味を持たない語
- 出力形式: JSON固定（自由文禁止）

注意:

- `03_merge_concepts.py` は `concepts.json` 内の `concepts` を読み込む実装であり、  
  sourceファイル内 `relationships` は自動で統合しない。
- 関係情報を反映したい場合は、`lbd-output/scs_concepts_db.json` 側へ追加するか、  
  関係統合処理を別途実装する。

---

## 7. 完了判定（目安）

最低条件:

- `lbd-output/scs_concepts_db.json` が生成される
- `lbd-output/knowledge_graph.json` が生成される
- `lbd-output/gap_candidates.json` が生成される
- `knowledge_graph.json.metadata.node_count > 0`
- `knowledge_graph.json.metadata.edge_count > 0`

このリポジトリの既存スナップショット（2026-02-12時点）では:

- `refs/*.pdf`: 91件
- `chunk_stats.total_chunks`: 1795
- `knowledge_graph`: 622ノード / 846エッジ

ただし、Phase 3の抽出方法と追加関係の有無でノード数・エッジ数は変動する。

---

## 8. 既知の再現性リスク

1. Phase 3がLLM抽出運用であり、完全決定論ではない  
2. `03_merge_concepts.py` は既存DBを読み込んでマージするため、過去成果の影響を受ける  
3. `04_build_knowledge_graph.py` は `lbd-output/inferred_relationships.json` が存在すると追加反映する

必要に応じて、クリーンコピー上で実行して差分混入を防ぐこと。

---

## 9. 最短実行コマンド（モードA）

```bash
cd "/Users/keigo/Documents/卒論作業ふぁいる　ローカル"
bash lbd-pipeline/scripts/01_extract_text.sh
python3 lbd-pipeline/scripts/02_chunk_texts.py
python3 lbd-pipeline/scripts/03_merge_concepts.py
python3 lbd-pipeline/scripts/04_build_knowledge_graph.py
```

