#!/usr/bin/env python3
"""
12_map_to_rq.py - Map concepts and predictions to thesis Research Questions

This script:
1. Loads concepts database and prediction results
2. Maps concepts to thesis RQs based on:
   - RQ1: 4-axis framework analysis (Task B results)
   - RQ2: Corporate impact analysis (Task A results)
   - RQ3: Japan implications (Task C results + JP concepts)
3. Generates structured markdown files for thesis writing

Output:
- rq1_four_axis_analysis.md
- rq2_corporate_impact.md
- rq3_japan_implications.md
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_rq1_report(concepts: list, predictions: dict) -> str:
    """Generate RQ1: 4-axis framework analysis report."""
    four_axis_scores = predictions.get('four_axis_scores', {}).get('predictions', [])

    # Create lookup
    score_lookup = {p['concept_id']: p for p in four_axis_scores}

    # Group by dominant axis
    axis_groups = defaultdict(list)
    for concept in concepts:
        cid = concept['concept_id']
        if cid in score_lookup:
            scores = score_lookup[cid].get('four_axis_scores', {})
            if scores:
                dominant = max(scores.items(), key=lambda x: x[1])
                axis_groups[dominant[0]].append({
                    'concept': concept,
                    'scores': scores,
                    'dominant_score': dominant[1]
                })

    # Japanese names for axes
    axis_names = {
        'governance': 'ガバナンス',
        'data_flow': 'データフロー',
        'incentive': 'インセンティブ設計',
        'public_private': '官民関係'
    }

    md = f"""# RQ1: 4軸フレームワーク分析

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概要

本章では、社会信用システム（SCS）の制度要素を4軸フレームワーク（ガバナンス、データフロー、インセンティブ設計、官民関係）に基づいて分析する。

### 軸別分布

| 軸 | 概念数 |
|----|--------|
"""
    for axis in ['governance', 'data_flow', 'incentive', 'public_private']:
        count = len(axis_groups.get(axis, []))
        md += f"| {axis_names.get(axis, axis)} | {count} |\n"

    for axis in ['governance', 'data_flow', 'incentive', 'public_private']:
        items = sorted(axis_groups.get(axis, []), key=lambda x: -x['dominant_score'])
        md += f"""
## {axis_names.get(axis, axis)}軸 ({len(items)}概念)

"""
        if items:
            md += "### 主要概念\n\n"
            for item in items[:10]:
                c = item['concept']
                scores = item['scores']
                md += f"""#### {c.get('jp_name', '')} ({c.get('en_name', '')})

- **スコア**: governance={scores.get('governance', 0):.2f}, data_flow={scores.get('data_flow', 0):.2f}, incentive={scores.get('incentive', 0):.2f}, public_private={scores.get('public_private', 0):.2f}
- **定義**: {c.get('definition', '-')}
- **出典**: {', '.join(c.get('source_papers', []))}

"""
    return md

def generate_rq2_report(concepts: list, predictions: dict) -> str:
    """Generate RQ2: Corporate impact analysis report."""
    corporate_impact = predictions.get('corporate_impact', {}).get('predictions', [])

    # Create lookup
    impact_lookup = {p['concept_id']: p for p in corporate_impact}

    # Group by impact labels
    impact_groups = defaultdict(list)
    for concept in concepts:
        cid = concept['concept_id']
        if cid in impact_lookup:
            labels = impact_lookup[cid].get('corporate_impact_labels', [])
            for label in labels:
                impact_groups[label].append(concept)

    # Organize by category
    benefit_labels = ['便益_金融アクセス', '便益_市場秩序', '便益_取引コスト削減']
    cost_labels = ['コスト_コンプライアンス', 'コスト_参入障壁']
    risk_labels = ['リスク_連鎖制裁', 'リスク_プライバシー', 'リスク_恣意的運用']

    md = f"""# RQ2: 企業経営環境への影響分析

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概要

本章では、SCSが企業経営環境にもたらす影響を「便益」「コスト」「リスク」の3カテゴリに分類して分析する。

### カテゴリ別分布

| カテゴリ | ラベル | 概念数 |
|---------|--------|--------|
"""
    for label in benefit_labels + cost_labels + risk_labels:
        count = len(impact_groups.get(label, []))
        category = label.split('_')[0]
        md += f"| {category} | {label} | {count} |\n"

    md += """
---

## 便益カテゴリ

企業が SCS から得られる正の効果。

"""
    for label in benefit_labels:
        items = impact_groups.get(label, [])
        md += f"""### {label} ({len(items)}概念)

"""
        for c in items[:5]:
            md += f"- **{c.get('jp_name', '')}**: {c.get('definition', '-')[:100]}...\n"
        if len(items) > 5:
            md += f"- ... 他 {len(items) - 5} 概念\n"
        md += "\n"

    md += """
---

## コストカテゴリ

SCS 対応に伴う企業の直接的負担。

"""
    for label in cost_labels:
        items = impact_groups.get(label, [])
        md += f"""### {label} ({len(items)}概念)

"""
        for c in items[:5]:
            md += f"- **{c.get('jp_name', '')}**: {c.get('definition', '-')[:100]}...\n"
        if len(items) > 5:
            md += f"- ... 他 {len(items) - 5} 概念\n"
        md += "\n"

    md += """
---

## リスクカテゴリ

SCS に伴う不確実性・潜在的損害。

"""
    for label in risk_labels:
        items = impact_groups.get(label, [])
        md += f"""### {label} ({len(items)}概念)

"""
        for c in items[:5]:
            md += f"- **{c.get('jp_name', '')}**: {c.get('definition', '-')[:100]}...\n"
        if len(items) > 5:
            md += f"- ... 他 {len(items) - 5} 概念\n"
        md += "\n"

    return md

def generate_rq3_report(concepts: list, predictions: dict) -> str:
    """Generate RQ3: Japan implications report."""
    transferability = predictions.get('transferability', {}).get('predictions', [])

    # Create lookup
    trans_lookup = {p['concept_id']: p for p in transferability}

    # Separate by recommendation
    recommended = []
    conditional = []
    not_recommended = []

    for concept in concepts:
        cid = concept['concept_id']
        if cid in trans_lookup:
            rec = trans_lookup[cid].get('transferability_recommendation', '')
            item = {'concept': concept, 'prediction': trans_lookup[cid]}
            if rec == '移転推奨':
                recommended.append(item)
            elif rec == '移転非推奨':
                not_recommended.append(item)
            else:
                conditional.append(item)

    # Get Japan-specific concepts
    jp_concepts = [c for c in concepts if c.get('country_tag') == 'JP']

    md = f"""# RQ3: 日本への示唆

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概要

本章では、中国 SCS の制度要素が日本にどの程度移転可能かを分析し、日本の既存制度との比較から政策的示唆を導出する。

### 移転可能性分布

| 推奨度 | 概念数 |
|--------|--------|
| 移転推奨 | {len(recommended)} |
| 条件付き移転可能 | {len(conditional)} |
| 移転非推奨 | {len(not_recommended)} |

---

## 日本関連概念 ({len(jp_concepts)}概念)

日本の既存制度・慣行に関する概念。

"""
    for c in jp_concepts:
        md += f"""### {c.get('jp_name', '')} ({c.get('en_name', '')})

- **定義**: {c.get('definition', '-')}
- **4軸**: {', '.join(c.get('four_axis', []))}
- **出典**: {', '.join(c.get('source_papers', []))}

"""

    md += """
---

## 移転推奨

透明性・救済メカニズムの観点から日本への導入が推奨される制度要素。

"""
    for item in recommended[:10]:
        c = item['concept']
        p = item['prediction']
        md += f"""### {c.get('jp_name', '')} ({c.get('en_name', '')})

- **推奨理由**: {p.get('transferability_reasoning', '-')}
- **定義**: {c.get('definition', '-')}

"""

    md += """
---

## 移転非推奨

透明性・比例原則・適正手続きの観点から日本への導入が困難な制度要素。

"""
    for item in not_recommended[:10]:
        c = item['concept']
        p = item['prediction']
        md += f"""### {c.get('jp_name', '')} ({c.get('en_name', '')})

- **非推奨理由**: {p.get('transferability_reasoning', '-')}
- **定義**: {c.get('definition', '-')}

"""

    md += """
---

## 中国SCSと日本制度の比較

| 中国SCS | 日本 | ギャップ | 示唆 |
|---------|------|---------|------|
| 信用中国（統一プラットフォーム） | JICC/CIC/KSC（分散3機関） | 統一 vs 分散 | 連携強化の余地 |
| 統一社会信用コード (USCI) | 法人番号 | 用途・連結範囲 | 活用範囲拡大検討 |
| 連合懲戒（多領域制裁） | 暴力団排除条項（限定的） | 対象・範囲 | 慎重な検討必要 |
| ブラックリスト（公開） | 反社データベース（非公開） | 透明性 vs 秘匿性 | 設計思想の相違 |
| 信用修復制度 | なし | 事後救済 | **導入検討の余地大** |
| 分類規制（信用ベース検査） | 一律対応 | 規制効率化 | **導入検討の余地大** |

"""
    return md

def main():
    # Setup paths
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    predictions_dir = base_dir / 'lbd-output' / 'predictions'
    output_dir = base_dir / 'lbd-output'

    print("=" * 60)
    print("RQ Mapping Script")
    print("=" * 60)

    # Load database
    print(f"\nLoading database from: {db_path}")
    db = load_json(db_path)
    concepts = db.get('concepts', [])
    print(f"Found {len(concepts)} concepts")

    # Load predictions
    predictions = {}
    pred_files = {
        'corporate_impact': 'corporate_impact.json',
        'four_axis_scores': 'four_axis_scores.json',
        'transferability': 'transferability.json'
    }

    for key, filename in pred_files.items():
        path = predictions_dir / filename
        if path.exists():
            print(f"Loading predictions: {path}")
            predictions[key] = load_json(path)
        else:
            print(f"Warning: Prediction file not found: {path}")
            predictions[key] = {}

    # Generate reports
    print("\nGenerating RQ1 report...")
    rq1_content = generate_rq1_report(concepts, predictions)
    rq1_path = output_dir / 'rq1_four_axis_analysis.md'
    with open(rq1_path, 'w', encoding='utf-8') as f:
        f.write(rq1_content)
    print(f"Saved: {rq1_path}")

    print("Generating RQ2 report...")
    rq2_content = generate_rq2_report(concepts, predictions)
    rq2_path = output_dir / 'rq2_corporate_impact.md'
    with open(rq2_path, 'w', encoding='utf-8') as f:
        f.write(rq2_content)
    print(f"Saved: {rq2_path}")

    print("Generating RQ3 report...")
    rq3_content = generate_rq3_report(concepts, predictions)
    rq3_path = output_dir / 'rq3_japan_implications.md'
    with open(rq3_path, 'w', encoding='utf-8') as f:
        f.write(rq3_content)
    print(f"Saved: {rq3_path}")

    print("\n" + "=" * 60)
    print("RQ Mapping Complete")
    print("=" * 60)
    print(f"  RQ1: {rq1_path}")
    print(f"  RQ2: {rq2_path}")
    print(f"  RQ3: {rq3_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
