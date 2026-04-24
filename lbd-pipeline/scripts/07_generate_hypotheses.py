#!/usr/bin/env python3
"""
07_generate_hypotheses.py - Generate research hypotheses from gap candidates

Uses Swanson ABC model gaps to generate testable hypotheses for the thesis.
"""

import json
from pathlib import Path
from datetime import datetime

def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_hypothesis(gap: dict, concepts_db: dict) -> dict:
    """Generate a research hypothesis from a gap candidate."""
    concept_a = gap.get('concept_a_label', '')
    concept_b = gap.get('concept_b_label', '')
    concept_c = gap.get('concept_c_label', '')

    # Find full concept info
    concepts_map = {c['concept_id']: c for c in concepts_db.get('concepts', [])}

    a_info = concepts_map.get(gap.get('concept_a'), {})
    b_info = concepts_map.get(gap.get('concept_b'), {})
    c_info = concepts_map.get(gap.get('concept_c'), {})

    # Get four_axis for each concept
    a_axes = set(a_info.get('four_axis', []))
    b_axes = set(b_info.get('four_axis', []))
    c_axes = set(c_info.get('four_axis', []))

    # Determine hypothesis type based on axis overlap
    shared_axes = a_axes & c_axes
    bridge_axes = b_axes - (a_axes | c_axes)

    if shared_axes:
        hypothesis_type = "共通軸仮説"
        axis_context = f"両概念は{', '.join(shared_axes)}軸を共有する"
    elif bridge_axes:
        hypothesis_type = "橋渡し仮説"
        axis_context = f"{concept_b}が{', '.join(bridge_axes)}軸で両者を媒介する"
    else:
        hypothesis_type = "探索的仮説"
        axis_context = "軸間の新たな関係性を示唆する"

    # Generate hypothesis statement
    hypothesis = f"「{concept_a}」と「{concept_c}」は「{concept_b}」を介して関連しており、{axis_context}可能性がある。"

    # Generate research questions
    research_questions = [
        f"{concept_a}は{concept_c}にどのような影響を与えるか？",
        f"{concept_b}は両者の関係においてどのような役割を果たすか？",
        f"この関係は企業経営環境にどのような示唆を持つか？"
    ]

    # Assess relevance to thesis RQs
    rq_relevance = []
    if any(kw in str([a_info, b_info, c_info]) for kw in ['ガバナンス', 'データフロー', 'インセンティブ', '官民']):
        rq_relevance.append("RQ1: 4軸フレームワーク分析への貢献")
    if any(kw in str([a_info, b_info, c_info]) for kw in ['企業', '融資', 'コスト', 'リスク', '便益']):
        rq_relevance.append("RQ2: 企業経営環境への影響分析への貢献")
    if any(kw in str([a_info, b_info, c_info]) for kw in ['透明性', '救済', '日本', '移転']):
        rq_relevance.append("RQ3: 制度移転可能性分析への貢献")

    return {
        "gap_id": gap.get('key', ''),
        "concept_a": concept_a,
        "concept_b": concept_b,
        "concept_c": concept_c,
        "hypothesis_type": hypothesis_type,
        "hypothesis": hypothesis,
        "axis_context": axis_context,
        "research_questions": research_questions,
        "rq_relevance": rq_relevance if rq_relevance else ["探索的研究への貢献"],
        "priority": "high" if len(rq_relevance) >= 2 else "medium" if rq_relevance else "low"
    }

def main():
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    gaps_path = base_dir / 'lbd-output' / 'gap_candidates.json'
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    output_path = base_dir / 'lbd-output' / 'hypotheses.json'
    md_output_path = base_dir / 'lbd-output' / 'hypotheses.md'

    print("=== Hypothesis Generator ===")
    print(f"Gaps: {gaps_path}")
    print(f"DB: {db_path}")
    print()

    # Load data
    gap_data = load_json(gaps_path)
    concepts_db = load_json(db_path)

    gaps = gap_data.get('gaps', [])
    print(f"Processing {len(gaps)} gap candidates")

    # Generate hypotheses
    hypotheses = []
    for gap in gaps[:20]:  # Process top 20 gaps
        hypothesis = generate_hypothesis(gap, concepts_db)
        hypotheses.append(hypothesis)

    # Save JSON
    output_data = {
        "metadata": {
            "total_hypotheses": len(hypotheses),
            "created_at": datetime.now().isoformat(),
            "method": "Swanson ABC Model Gap Analysis"
        },
        "hypotheses": hypotheses
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON: {output_path}")

    # Generate Markdown report
    md_content = generate_markdown_report(hypotheses)
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"Saved Markdown: {md_output_path}")

    # Summary
    print()
    print("=== Summary ===")
    priority_counts = {}
    type_counts = {}
    for h in hypotheses:
        priority_counts[h['priority']] = priority_counts.get(h['priority'], 0) + 1
        type_counts[h['hypothesis_type']] = type_counts.get(h['hypothesis_type'], 0) + 1

    print("Priority Distribution:")
    for p, c in sorted(priority_counts.items()):
        print(f"  {p}: {c}")

    print("\nHypothesis Type Distribution:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")

def generate_markdown_report(hypotheses: list) -> str:
    """Generate a Markdown report from hypotheses."""
    lines = [
        "# SCS研究仮説レポート",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 概要",
        "",
        f"Swanson ABCモデルに基づくギャップ分析により、{len(hypotheses)}件の研究仮説を生成しました。",
        "",
        "## 高優先度仮説",
        ""
    ]

    # High priority hypotheses
    high_priority = [h for h in hypotheses if h['priority'] == 'high']
    for i, h in enumerate(high_priority, 1):
        lines.extend([
            f"### 仮説 {i}: {h['concept_a']} ⟷ {h['concept_b']} ⟷ {h['concept_c']}",
            "",
            f"**類型**: {h['hypothesis_type']}",
            "",
            f"**仮説**: {h['hypothesis']}",
            "",
            "**研究課題**:",
            ""
        ])
        for rq in h['research_questions']:
            lines.append(f"- {rq}")
        lines.extend([
            "",
            "**RQ関連性**:",
            ""
        ])
        for rel in h['rq_relevance']:
            lines.append(f"- {rel}")
        lines.extend(["", "---", ""])

    # Medium priority hypotheses
    lines.extend([
        "## 中優先度仮説",
        ""
    ])
    medium_priority = [h for h in hypotheses if h['priority'] == 'medium']
    for h in medium_priority[:5]:  # Show first 5
        lines.extend([
            f"- **{h['concept_a']} ⟷ {h['concept_b']} ⟷ {h['concept_c']}**: {h['hypothesis'][:80]}...",
            ""
        ])

    # Statistics
    lines.extend([
        "## 統計情報",
        "",
        f"- 総仮説数: {len(hypotheses)}",
        f"- 高優先度: {len(high_priority)}",
        f"- 中優先度: {len(medium_priority)}",
        f"- 低優先度: {len([h for h in hypotheses if h['priority'] == 'low'])}",
        ""
    ])

    return '\n'.join(lines)

if __name__ == '__main__':
    main()
