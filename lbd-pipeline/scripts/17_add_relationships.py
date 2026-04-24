#!/usr/bin/env python3
"""
17_add_relationships.py - Add manual relationships to knowledge graph

This script:
1. Reads manual_relationships.json with predefined edges
2. Validates that all referenced nodes exist
3. Adds edges to knowledge_graph.json
4. Updates scs_concepts_db.json with related_concepts
5. Reports isolated node reduction
"""

import json
from pathlib import Path
from datetime import datetime


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, path: Path):
    """Save JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_isolated_nodes(kg: dict) -> set:
    """Get set of isolated node IDs."""
    all_nodes = {n['id'] for n in kg['nodes']}
    connected = set()
    for e in kg['edges']:
        connected.add(e['source'])
        connected.add(e['target'])
    return all_nodes - connected


def count_by_country(node_ids: set, kg: dict) -> dict:
    """Count nodes by country tag."""
    node_info = {n['id']: n for n in kg['nodes']}
    counts = {}
    for nid in node_ids:
        if nid in node_info:
            country = node_info[nid].get('country_tag', 'unknown')
            counts[country] = counts.get(country, 0) + 1
    return counts


def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    relationships_path = base_dir / 'lbd-output' / 'manual_relationships.json'
    kg_path = base_dir / 'lbd-output' / 'knowledge_graph.json'
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'

    print("=" * 60)
    print("Add Manual Relationships to Knowledge Graph")
    print("=" * 60)
    print(f"Relationships file: {relationships_path}")
    print(f"Knowledge graph: {kg_path}")
    print(f"Database: {db_path}")
    print()

    # Load files
    print("Loading files...")
    relationships = load_json(relationships_path)
    kg = load_json(kg_path)
    db = load_json(db_path)

    # Get existing state
    existing_edges = {(e['source'], e['target']) for e in kg['edges']}
    existing_edges.update({(e['target'], e['source']) for e in kg['edges']})
    all_node_ids = {n['id'] for n in kg['nodes']}

    isolated_before = get_isolated_nodes(kg)
    by_country_before = count_by_country(isolated_before, kg)

    print(f"Existing nodes: {len(all_node_ids)}")
    print(f"Existing edges: {len(kg['edges'])}")
    print(f"Isolated before: {len(isolated_before)}")
    print(f"  By country: {by_country_before}")
    print()

    # Process relationships
    print("Processing relationships...")
    added_count = 0
    skipped_count = 0
    missing_nodes = []

    for category in relationships['relationships']:
        cat_name = category['category']
        cat_added = 0

        for edge in category['edges']:
            source = edge['source']
            target = edge['target']
            edge_type = edge['type']

            # Validate nodes exist
            if source not in all_node_ids:
                missing_nodes.append(f"{source} (source in {cat_name})")
                continue
            if target not in all_node_ids:
                missing_nodes.append(f"{target} (target in {cat_name})")
                continue

            # Check for duplicate
            if (source, target) in existing_edges:
                skipped_count += 1
                continue

            # Add edge to KG
            kg['edges'].append({
                'source': source,
                'target': target,
                'type': edge_type,
                'weight': 1.0,
                'manual': True
            })

            # Track as existing to prevent duplicates within this run
            existing_edges.add((source, target))
            existing_edges.add((target, source))

            added_count += 1
            cat_added += 1

        print(f"  {cat_name}: {cat_added} edges added")

    print()

    # Report missing nodes
    if missing_nodes:
        print(f"WARNING: {len(missing_nodes)} missing node references:")
        for node in missing_nodes[:10]:
            print(f"  - {node}")
        if len(missing_nodes) > 10:
            print(f"  ... and {len(missing_nodes) - 10} more")
        print()

    # Update KG metadata
    kg['metadata']['edge_count'] = len(kg['edges'])
    kg['metadata']['manual_edges_added'] = {
        'timestamp': datetime.now().isoformat(),
        'count': added_count
    }

    # Calculate new isolated state
    isolated_after = get_isolated_nodes(kg)
    by_country_after = count_by_country(isolated_after, kg)

    # Save KG
    print("Saving knowledge graph...")
    save_json(kg, kg_path)

    # Update database related_concepts
    print("Updating database related_concepts...")
    concept_by_id = {c['concept_id']: c for c in db['concepts']}

    for category in relationships['relationships']:
        for edge in category['edges']:
            source = edge['source']
            target = edge['target']

            # Add to related_concepts in both directions
            if source in concept_by_id:
                if 'related_concepts' not in concept_by_id[source]:
                    concept_by_id[source]['related_concepts'] = []
                if target not in concept_by_id[source]['related_concepts']:
                    concept_by_id[source]['related_concepts'].append(target)

            if target in concept_by_id:
                if 'related_concepts' not in concept_by_id[target]:
                    concept_by_id[target]['related_concepts'] = []
                if source not in concept_by_id[target]['related_concepts']:
                    concept_by_id[target]['related_concepts'].append(source)

    # Update DB metadata
    db['metadata']['last_updated'] = datetime.now().isoformat()
    db['metadata']['manual_relationships_added'] = {
        'timestamp': datetime.now().isoformat(),
        'count': added_count
    }

    # Save DB
    save_json(db, db_path)

    # Print summary
    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Edges added: {added_count}")
    print(f"Edges skipped (duplicate): {skipped_count}")
    print(f"Missing nodes: {len(missing_nodes)}")
    print()
    print("Isolated nodes:")
    print(f"  Before: {len(isolated_before)}")
    print(f"  After:  {len(isolated_after)}")
    print(f"  Reduction: {len(isolated_before) - len(isolated_after)}")
    print()
    print("By country (before → after):")
    for country in ['JP', 'EU', 'US', 'CN']:
        before = by_country_before.get(country, 0)
        after = by_country_after.get(country, 0)
        print(f"  {country}: {before} → {after}")

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run 08_build_visualization.py to update visualization")
    print("  2. Optionally run 16_regenerate_gaps.py for new gap detection")


if __name__ == '__main__':
    main()
