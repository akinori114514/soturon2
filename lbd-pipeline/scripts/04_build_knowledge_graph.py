#!/usr/bin/env python3
"""
04_build_knowledge_graph.py - Build knowledge graph from concepts database

Creates:
1. knowledge_graph.json - Graph structure for visualization
2. gap_candidates.json - Swanson ABC model gap candidates
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from itertools import combinations

def load_concepts_db(db_path: Path) -> dict:
    """Load concepts database."""
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_graph(db: dict) -> dict:
    """Build graph structure for visualization."""
    concepts = db.get('concepts', [])
    relationships = db.get('relationships', [])

    # Build nodes
    nodes = []
    for concept in concepts:
        node = {
            "id": concept['concept_id'],
            "label": concept.get('jp_name', concept.get('en_name', '')),
            "en_label": concept.get('en_name', ''),
            "zh_name": concept.get('zh_name', ''),
            "aliases": concept.get('aliases', []),
            "type": concept.get('concept_type', 'unknown'),
            "four_axis": concept.get('four_axis', []),
            "sources": concept.get('source_papers', []),
            "definition": concept.get('definition', ''),
            "country_tag": concept.get('country_tag', 'CN'),
            # Visualization properties
            "size": len(concept.get('source_papers', [])) * 5 + 10,
            "color": get_axis_color(concept.get('four_axis', []))
        }
        nodes.append(node)

    # Build edges
    edges = []
    for rel in relationships:
        edge = {
            "id": f"{rel['source']}-{rel['target']}",
            "source": rel['source'],
            "target": rel['target'],
            "type": rel.get('type', 'reference'),
            "label": rel.get('description', ''),
            # Visualization properties
            "width": get_edge_width(rel.get('type', '')),
            "style": get_edge_style(rel.get('type', ''))
        }
        edges.append(edge)

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "created_at": datetime.now().isoformat()
        }
    }

def get_axis_color(axes: list) -> str:
    """Generate color based on 4-axis composition."""
    # Color mapping for each axis
    axis_colors = {
        "ガバナンス": (231, 76, 60),      # Red
        "データフロー": (52, 152, 219),    # Blue
        "インセンティブ設計": (46, 204, 113),  # Green
        "官民関係": (155, 89, 182)         # Purple
    }

    if not axes:
        return "#95a5a6"  # Gray for unknown

    # Mix colors based on axes present
    r, g, b = 0, 0, 0
    count = 0
    for axis in axes:
        if axis in axis_colors:
            ar, ag, ab = axis_colors[axis]
            r += ar
            g += ag
            b += ab
            count += 1

    if count > 0:
        r, g, b = r // count, g // count, b // count
        return f"#{r:02x}{g:02x}{b:02x}"

    return "#95a5a6"

def get_edge_width(rel_type: str) -> int:
    """Get edge width based on relationship type."""
    widths = {
        "subsumption": 3,
        "implementation": 2,
        "causal": 4,
        "comparison": 2,
        "co_occurrence": 1,
        "reference": 1
    }
    return widths.get(rel_type, 1)

def get_edge_style(rel_type: str) -> str:
    """Get edge style based on relationship type."""
    styles = {
        "subsumption": "solid",
        "implementation": "dashed",
        "causal": "solid",
        "comparison": "dotted",
        "co_occurrence": "dotted",
        "reference": "dashed"
    }
    return styles.get(rel_type, "solid")

def detect_gaps(graph: dict) -> list[dict]:
    """
    Detect potential research gaps using Swanson ABC model.

    Find pairs of nodes (A, C) that are not directly connected
    but share common neighbors (B).
    """
    nodes = {n['id']: n for n in graph['nodes']}
    edges = graph['edges']

    # Build adjacency list
    adjacency = defaultdict(set)
    for edge in edges:
        adjacency[edge['source']].add(edge['target'])
        adjacency[edge['target']].add(edge['source'])

    # Find indirect connections (A-B-C where A-C is not connected)
    gaps = []

    for node_id, neighbors in adjacency.items():
        # For each pair of neighbors
        for n1, n2 in combinations(neighbors, 2):
            # Check if n1 and n2 are NOT directly connected
            if n2 not in adjacency[n1]:
                # Found a gap: n1 -- node_id -- n2
                gap = {
                    "concept_a": n1,
                    "concept_a_label": nodes.get(n1, {}).get('label', n1),
                    "concept_b": node_id,
                    "concept_b_label": nodes.get(node_id, {}).get('label', node_id),
                    "concept_c": n2,
                    "concept_c_label": nodes.get(n2, {}).get('label', n2),
                    "gap_type": "indirect_connection",
                    "hypothesis_prompt": f"「{nodes.get(n1, {}).get('label', n1)}」と「{nodes.get(n2, {}).get('label', n2)}」は「{nodes.get(node_id, {}).get('label', node_id)}」を介して間接的に関連している可能性がある。この関係を検証する価値があるか？"
                }

                # Avoid duplicates (A-B-C == C-B-A)
                gap_key = tuple(sorted([n1, n2]) + [node_id])
                gap['key'] = f"{gap_key[0]}-{gap_key[2]}-{gap_key[1]}"

                if not any(g.get('key') == gap['key'] for g in gaps):
                    gaps.append(gap)

    # Sort by relevance (number of shared neighbors)
    gaps.sort(key=lambda g: len(adjacency[g['concept_b']]), reverse=True)

    return gaps[:50]  # Return top 50 gaps

def load_inferred_relationships(inferred_path: Path, min_confidence: float = 0.4) -> list:
    """Load inferred relationships from is-a inference script."""
    if not inferred_path.exists():
        return []

    with open(inferred_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    relationships = data.get('relationships', [])

    # Filter by confidence
    filtered = [
        r for r in relationships
        if r.get('similarity', {}).get('heuristic_confidence', 0) >= min_confidence
    ]

    return filtered


def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    inferred_path = base_dir / 'lbd-output' / 'inferred_relationships.json'
    graph_output = base_dir / 'lbd-output' / 'knowledge_graph.json'
    gaps_output = base_dir / 'lbd-output' / 'gap_candidates.json'

    print("=== Knowledge Graph Builder ===")
    print(f"Input: {db_path}")
    print()

    # Load database
    db = load_concepts_db(db_path)

    # Load inferred relationships (from 13_infer_hierarchy.py)
    inferred_rels = load_inferred_relationships(inferred_path, min_confidence=0.4)
    if inferred_rels:
        print(f"Loading {len(inferred_rels)} inferred relationships (confidence >= 0.4)")

        # Create a set of existing relationship pairs to avoid duplicates
        existing_pairs = set()
        for rel in db.get('relationships', []):
            existing_pairs.add((rel['source'], rel['target']))
            existing_pairs.add((rel['target'], rel['source']))

        # Add inferred relationships that don't already exist
        added = 0
        for inf_rel in inferred_rels:
            pair = (inf_rel['source'], inf_rel['target'])
            if pair not in existing_pairs and (pair[1], pair[0]) not in existing_pairs:
                db['relationships'].append({
                    'source': inf_rel['source'],
                    'target': inf_rel['target'],
                    'type': inf_rel.get('type', 'subsumption'),
                    'description': inf_rel.get('description', ''),
                    'inferred': True
                })
                existing_pairs.add(pair)
                added += 1

        print(f"Added {added} new inferred relationships")

    # Build graph
    graph = build_graph(db)
    print(f"Graph nodes: {graph['metadata']['node_count']}")
    print(f"Graph edges: {graph['metadata']['edge_count']}")

    # Save graph
    with open(graph_output, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"Saved graph to: {graph_output}")

    # Detect gaps
    gaps = detect_gaps(graph)
    print(f"Gap candidates found: {len(gaps)}")

    # Save gaps
    gap_data = {
        "metadata": {
            "total_gaps": len(gaps),
            "created_at": datetime.now().isoformat(),
            "method": "Swanson ABC model"
        },
        "gaps": gaps
    }
    with open(gaps_output, 'w', encoding='utf-8') as f:
        json.dump(gap_data, f, ensure_ascii=False, indent=2)
    print(f"Saved gaps to: {gaps_output}")

if __name__ == '__main__':
    main()
