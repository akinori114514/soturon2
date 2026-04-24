#!/usr/bin/env python3
"""
16_regenerate_gaps.py - Regenerate gap candidates with improved algorithm

This script:
1. Excludes hub nodes (degree > 15) as bridges
2. Ensures bridge diversity (max 5 gaps per bridge)
3. Prioritizes cross-country gaps (RQ3)
4. Scores and ranks gaps for research value
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter


def load_knowledge_graph(kg_path: Path) -> dict:
    """Load knowledge graph."""
    with open(kg_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_adjacency_and_degrees(kg: dict) -> tuple[dict, dict]:
    """Build adjacency list and calculate degrees."""
    adj = defaultdict(set)
    for e in kg['edges']:
        adj[e['source']].add(e['target'])
        adj[e['target']].add(e['source'])

    degrees = {node: len(neighbors) for node, neighbors in adj.items()}
    return dict(adj), degrees


def find_gaps(kg: dict, adj: dict, degrees: dict, hub_threshold: int = 15) -> list[dict]:
    """
    Find all A-B-C gaps where:
    - A and C are NOT directly connected
    - B is NOT a hub node (degree > threshold)
    """
    # Identify hub nodes to exclude
    hubs = {n for n, d in degrees.items() if d > hub_threshold}
    print(f"Hub nodes excluded (degree > {hub_threshold}): {len(hubs)}")
    for hub in sorted(hubs, key=lambda x: -degrees[x])[:5]:
        node_info = next((n for n in kg['nodes'] if n['id'] == hub), {})
        print(f"  - {node_info.get('label', hub)} (degree={degrees[hub]})")

    # Build node info lookup
    node_info = {n['id']: n for n in kg['nodes']}

    # Find gaps through non-hub bridges
    gaps = []
    non_hub_bridges = set(adj.keys()) - hubs

    for b in non_hub_bridges:
        b_neighbors = list(adj[b])
        if len(b_neighbors) < 2:
            continue

        for i, a in enumerate(b_neighbors):
            for c in b_neighbors[i+1:]:
                # Check if A-C are NOT directly connected
                if c not in adj.get(a, set()):
                    a_info = node_info.get(a, {})
                    b_info = node_info.get(b, {})
                    c_info = node_info.get(c, {})

                    gaps.append({
                        'a': a,
                        'a_label': a_info.get('label', '?'),
                        'a_country': a_info.get('country_tag', 'CN'),
                        'a_type': a_info.get('concept_type', 'unknown'),
                        'b': b,
                        'b_label': b_info.get('label', '?'),
                        'b_degree': degrees.get(b, 0),
                        'c': c,
                        'c_label': c_info.get('label', '?'),
                        'c_country': c_info.get('country_tag', 'CN'),
                        'c_type': c_info.get('concept_type', 'unknown'),
                    })

    return gaps


def score_gaps(gaps: list[dict]) -> list[dict]:
    """
    Score gaps for research value:
    - Cross-country bonus: +2.0
    - Different concept type bonus: +0.5
    - Low bridge degree bonus: +1.0/degree
    """
    for gap in gaps:
        score = 1.0

        # Cross-country bonus (RQ3 relevance)
        if gap['a_country'] != gap['c_country']:
            score += 2.0
            gap['cross_country'] = True
        else:
            gap['cross_country'] = False

        # Different type bonus
        if gap['a_type'] != gap['c_type']:
            score += 0.5

        # Low degree bridge bonus (more specific connection)
        if gap['b_degree'] > 0:
            score += 1.0 / gap['b_degree']

        gap['score'] = round(score, 3)

    return gaps


def diversify_gaps(gaps: list[dict], max_per_bridge: int = 5, total_limit: int = 50) -> list[dict]:
    """
    Select diverse gaps:
    - Limit gaps per bridge concept
    - Prioritize high-scoring gaps
    """
    # Sort by score descending
    gaps.sort(key=lambda x: -x['score'])

    bridge_counts = Counter()
    selected = []

    for gap in gaps:
        bridge = gap['b']
        if bridge_counts[bridge] < max_per_bridge:
            selected.append(gap)
            bridge_counts[bridge] += 1

        if len(selected) >= total_limit:
            break

    return selected


def generate_hypothesis_prompt(gap: dict) -> str:
    """Generate research hypothesis prompt for a gap."""
    if gap['cross_country']:
        return (
            f"「{gap['a_label']}」({gap['a_country']})と"
            f"「{gap['c_label']}」({gap['c_country']})は"
            f"「{gap['b_label']}」を介して間接的に関連している。"
            f"この異国間の関係性から、どのような比較制度的示唆が得られるか？"
        )
    else:
        return (
            f"「{gap['a_label']}」と「{gap['c_label']}」は"
            f"「{gap['b_label']}」を介して間接的に関連している可能性がある。"
            f"この関係を検証する価値があるか？"
        )


def save_gap_candidates(gaps: list[dict], output_path: Path):
    """Save gap candidates to JSON."""
    output = {
        "metadata": {
            "total_gaps": len(gaps),
            "created_at": datetime.now().isoformat(),
            "method": "Swanson ABC model (improved)",
            "improvements": [
                "Hub node exclusion (degree > 15)",
                "Bridge diversity (max 5 per bridge)",
                "Cross-country prioritization",
                "Score-based ranking"
            ]
        },
        "gaps": [
            {
                "concept_a": g['a'],
                "concept_a_label": g['a_label'],
                "concept_a_country": g['a_country'],
                "concept_b": g['b'],
                "concept_b_label": g['b_label'],
                "concept_c": g['c'],
                "concept_c_label": g['c_label'],
                "concept_c_country": g['c_country'],
                "gap_type": "cross_country" if g['cross_country'] else "indirect_connection",
                "score": g['score'],
                "hypothesis_prompt": generate_hypothesis_prompt(g),
                "key": f"{g['a']}-{g['b']}-{g['c']}"
            }
            for g in gaps
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def generate_hypotheses_md(gaps: list[dict], output_path: Path):
    """Generate hypotheses markdown report."""
    lines = [
        "# SCS研究仮説レポート (v2 - 改善版)",
        "",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 概要",
        "",
        "改善されたSwanson ABCモデルに基づくギャップ分析により、研究仮説を生成しました。",
        "",
        "### 改善点",
        "- ハブノード（ブラックリスト、社会信用システム等）を橋渡し概念から除外",
        "- 橋渡し概念の多様性を確保（同一概念は最大5件まで）",
        "- 異国間ギャップを優先（RQ3対応）",
        "",
        f"**生成ギャップ数**: {len(gaps)}件",
        f"**異国間ギャップ**: {sum(1 for g in gaps if g['cross_country'])}件",
        "",
        "---",
        "",
        "## 高優先度仮説（異国間）",
        ""
    ]

    # Cross-country hypotheses first
    cross_country = [g for g in gaps if g['cross_country']]
    same_country = [g for g in gaps if not g['cross_country']]

    for i, gap in enumerate(cross_country[:15], 1):
        lines.extend([
            f"### 仮説 {i}: {gap['a_label']} ({gap['a_country']}) ⟷ {gap['b_label']} ⟷ {gap['c_label']} ({gap['c_country']})",
            "",
            f"**スコア**: {gap['score']}",
            "",
            f"**類型**: 異国間比較仮説",
            "",
            f"**仮説**: {generate_hypothesis_prompt(gap)}",
            "",
            "**研究課題**:",
            "",
            f"- {gap['a_label']}と{gap['c_label']}の制度的差異は何か？",
            f"- {gap['b_label']}は両国でどのように機能しているか？",
            "- この比較から日本への示唆として何が得られるか？（RQ3）",
            "",
            "---",
            ""
        ])

    lines.extend([
        "",
        "## 探索的仮説（同一国内）",
        ""
    ])

    for i, gap in enumerate(same_country[:5], len(cross_country[:15]) + 1):
        lines.extend([
            f"### 仮説 {i}: {gap['a_label']} ⟷ {gap['b_label']} ⟷ {gap['c_label']}",
            "",
            f"**スコア**: {gap['score']}",
            "",
            f"**類型**: 間接関連仮説",
            "",
            f"**仮説**: {generate_hypothesis_prompt(gap)}",
            "",
            "---",
            ""
        ])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    kg_path = base_dir / 'lbd-output' / 'knowledge_graph.json'
    gap_output = base_dir / 'lbd-output' / 'gap_candidates_v2.json'
    hypothesis_output = base_dir / 'lbd-output' / 'hypotheses_v2.md'

    print("=" * 60)
    print("Gap Regeneration (Improved Algorithm)")
    print("=" * 60)
    print(f"Knowledge graph: {kg_path}")
    print()

    # Load KG
    kg = load_knowledge_graph(kg_path)
    print(f"Loaded: {len(kg['nodes'])} nodes, {len(kg['edges'])} edges")
    print()

    # Build adjacency and degrees
    adj, degrees = build_adjacency_and_degrees(kg)

    # Find gaps
    print("Finding gaps (excluding hub nodes)...")
    all_gaps = find_gaps(kg, adj, degrees, hub_threshold=15)
    print(f"Found {len(all_gaps)} total gaps")
    print()

    # Score gaps
    print("Scoring gaps...")
    scored_gaps = score_gaps(all_gaps)

    cross_country = sum(1 for g in scored_gaps if g['cross_country'])
    print(f"Cross-country gaps: {cross_country}")
    print()

    # Diversify and select top gaps
    print("Selecting diverse top gaps...")
    selected_gaps = diversify_gaps(scored_gaps, max_per_bridge=5, total_limit=50)
    print(f"Selected: {len(selected_gaps)} gaps")

    # Analyze selection
    bridge_diversity = len(set(g['b'] for g in selected_gaps))
    a_diversity = len(set(g['a'] for g in selected_gaps))
    c_diversity = len(set(g['c'] for g in selected_gaps))
    cross_selected = sum(1 for g in selected_gaps if g['cross_country'])

    print()
    print("Selection statistics:")
    print(f"  Unique bridges: {bridge_diversity}")
    print(f"  Unique A endpoints: {a_diversity}")
    print(f"  Unique C endpoints: {c_diversity}")
    print(f"  Cross-country: {cross_selected}")
    print()

    # Save outputs
    print("Saving outputs...")
    save_gap_candidates(selected_gaps, gap_output)
    print(f"  Gap candidates: {gap_output}")

    generate_hypotheses_md(selected_gaps, hypothesis_output)
    print(f"  Hypotheses: {hypothesis_output}")

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
