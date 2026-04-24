#!/usr/bin/env python3
"""
14_apply_merge.py - Apply merge candidates to concepts database

This script:
1. Reads merge_candidates.json
2. Merges concept pairs based on confidence level
3. Updates scs_concepts_db.json
4. Updates references (related_concepts, relationships)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


def load_merge_candidates(path: Path) -> dict:
    """Load merge candidates from JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_concepts_db(path: Path) -> dict:
    """Load concepts database."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_concepts(db: dict, concept_a_id: str, concept_b_id: str) -> bool:
    """
    Merge concept B into concept A.

    - Combines source_papers, context_quotes, four_axis
    - Removes concept B from the database
    - Updates all references to concept B -> concept A

    Returns True if merge was successful.
    """
    concepts = db.get('concepts', [])

    # Find concepts
    concept_a = None
    concept_b = None
    concept_a_idx = None
    concept_b_idx = None

    for i, c in enumerate(concepts):
        if c['concept_id'] == concept_a_id:
            concept_a = c
            concept_a_idx = i
        elif c['concept_id'] == concept_b_id:
            concept_b = c
            concept_b_idx = i

    if concept_a is None or concept_b is None:
        print(f"  Warning: Could not find concepts {concept_a_id} or {concept_b_id}")
        return False

    # Merge source_papers
    existing_sources = set(concept_a.get('source_papers', []))
    new_sources = set(concept_b.get('source_papers', []))
    concept_a['source_papers'] = list(existing_sources | new_sources)

    # Merge context_quotes (deduplicated, max 5)
    existing_quotes = concept_a.get('context_quotes', [])
    new_quotes = concept_b.get('context_quotes', [])
    all_quotes = list(set(existing_quotes + new_quotes))
    concept_a['context_quotes'] = all_quotes[:5]

    # Merge four_axis
    existing_axes = set(concept_a.get('four_axis', []))
    new_axes = set(concept_b.get('four_axis', []))
    concept_a['four_axis'] = list(existing_axes | new_axes)

    # Merge related_concepts
    existing_related = set(concept_a.get('related_concepts', []))
    new_related = set(concept_b.get('related_concepts', []))
    # Remove self-references
    merged_related = (existing_related | new_related) - {concept_a_id, concept_b_id}
    concept_a['related_concepts'] = list(merged_related)

    # Add merge note
    if 'merge_history' not in concept_a:
        concept_a['merge_history'] = []
    concept_a['merge_history'].append({
        'merged_from': concept_b_id,
        'merged_at': datetime.now().isoformat(),
        'original_name': concept_b.get('en_name', '')
    })

    # Remove concept B
    del concepts[concept_b_idx]

    # Update all references to concept B -> concept A
    for c in concepts:
        if 'related_concepts' in c:
            c['related_concepts'] = [
                concept_a_id if rc == concept_b_id else rc
                for rc in c['related_concepts']
            ]

    # Update relationships
    relationships = db.get('relationships', [])
    updated_rels = []
    for rel in relationships:
        # Update source/target references
        if rel['source'] == concept_b_id:
            rel['source'] = concept_a_id
        if rel['target'] == concept_b_id:
            rel['target'] = concept_a_id

        # Skip self-referential relationships
        if rel['source'] != rel['target']:
            updated_rels.append(rel)

    db['relationships'] = updated_rels

    return True


def main():
    parser = argparse.ArgumentParser(description='Apply merge candidates to concepts database')
    parser.add_argument('--confidence', choices=['high', 'medium', 'all'], default='high',
                        help='Confidence level to merge (default: high)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be merged without making changes')
    args = parser.parse_args()

    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    merge_path = base_dir / 'lbd-output' / 'merge_candidates.json'
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'

    print("=" * 60)
    print("Apply Merge Candidates")
    print("=" * 60)
    print(f"Confidence level: {args.confidence}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Load data
    merge_data = load_merge_candidates(merge_path)
    db = load_concepts_db(db_path)

    candidates = merge_data.get('merge_candidates', [])

    # Filter by confidence
    if args.confidence == 'high':
        to_merge = [c for c in candidates if c.get('confidence') == 'high']
    elif args.confidence == 'medium':
        to_merge = [c for c in candidates if c.get('confidence') in ['high', 'medium']]
    else:
        to_merge = candidates

    print(f"Total candidates: {len(candidates)}")
    print(f"To merge ({args.confidence}): {len(to_merge)}")
    print()

    # Show merge plan
    print("Merge plan:")
    print("-" * 60)
    for i, candidate in enumerate(to_merge, 1):
        a = candidate['concept_a']
        b = candidate['concept_b']
        sim = candidate['similarity'].get('embedding_cos', 0)
        print(f"{i}. {a['id']} <- {b['id']} (sim={sim:.3f})")
        print(f"   {a['jp_name']} <- {b['jp_name']}")
    print("-" * 60)
    print()

    if args.dry_run:
        print("Dry run complete. No changes made.")
        return

    # Apply merges
    print("Applying merges...")
    merged_count = 0
    for candidate in to_merge:
        a_id = candidate['concept_a']['id']
        b_id = candidate['concept_b']['id']

        success = merge_concepts(db, a_id, b_id)
        if success:
            merged_count += 1
            print(f"  Merged: {b_id} -> {a_id}")
        else:
            print(f"  Failed: {a_id} <- {b_id}")

    # Update metadata
    db['metadata']['last_updated'] = datetime.now().isoformat()
    db['metadata']['merge_applied'] = {
        'timestamp': datetime.now().isoformat(),
        'confidence_level': args.confidence,
        'merged_count': merged_count
    }

    # Save
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"Merged: {merged_count} concept pairs")
    print(f"Concepts before: {len(to_merge) + len(db['concepts'])}")
    print(f"Concepts after: {len(db['concepts'])}")
    print(f"Saved to: {db_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
