#!/usr/bin/env python3
"""
03_merge_concepts.py - Merge extracted concepts into unified database

This script:
1. Loads existing concepts from scs_concepts_db.json
2. Loads new concepts from lbd-pipeline/concepts/
3. Deduplicates and merges
4. Outputs updated scs_concepts_db.json
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_existing_db(db_path: Path) -> dict:
    """Load existing concepts database."""
    if db_path.exists():
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "metadata": {
            "created": datetime.now().strftime("%Y-%m-%d"),
            "description": "SCS Literature-Based Discovery Database",
            "version": "2.0",
            "schema_version": "1.0"
        },
        "sources": [],
        "concepts": [],
        "relationships": []
    }

def load_new_concepts(concepts_dir: Path) -> list[dict]:
    """Load all newly extracted concepts from individual files."""
    all_concepts = []

    for source_dir in sorted(concepts_dir.iterdir()):
        if not source_dir.is_dir():
            continue

        # Look for merged concept file or individual chunks
        merged_file = source_dir / "concepts.json"
        if merged_file.exists():
            with open(merged_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'concepts' in data:
                    all_concepts.extend(data['concepts'])
        else:
            # Load from individual chunk files (any .json file)
            for chunk_file in sorted(source_dir.glob("*.json")):
                try:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'concepts' in data:
                            all_concepts.extend(data['concepts'])
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Warning: Could not parse {chunk_file}: {e}")

    return all_concepts

def deduplicate_concepts(concepts: list[dict]) -> list[dict]:
    """Remove duplicate concepts based on name matching."""
    seen = {}  # en_name -> concept

    for concept in concepts:
        en_name = concept.get('en_name', '').lower().strip()
        jp_name = concept.get('jp_name', '').strip()

        # Use English name as primary key, fallback to Japanese
        key = en_name if en_name else jp_name.lower()

        if not key:
            continue

        if key in seen:
            # Merge: combine source_papers, context_quotes, etc.
            existing = seen[key]

            # Merge source_papers
            existing_sources = set(existing.get('source_papers', []))
            new_sources = set(concept.get('source_papers', []))
            existing['source_papers'] = list(existing_sources | new_sources)

            # Merge context_quotes (deduplicated)
            existing_quotes = existing.get('context_quotes', [])
            new_quotes = concept.get('context_quotes', [])
            all_quotes = list(set(existing_quotes + new_quotes))
            existing['context_quotes'] = all_quotes[:5]  # Keep top 5

            # Merge four_axis
            existing_axes = set(existing.get('four_axis', []))
            new_axes = set(concept.get('four_axis', []))
            existing['four_axis'] = list(existing_axes | new_axes)
        else:
            seen[key] = concept.copy()

    return list(seen.values())

def assign_concept_ids(concepts: list[dict], start_id: int = 1) -> list[dict]:
    """Assign unique IDs to concepts."""
    for i, concept in enumerate(concepts, start=start_id):
        if 'concept_id' not in concept:
            concept['concept_id'] = f"SCS-{i:04d}"
    return concepts

def detect_relationships(concepts: list[dict]) -> list[dict]:
    """Detect relationships between concepts based on text matching."""
    relationships = []

    # Build name -> concept_id mapping
    name_to_id = {}
    for concept in concepts:
        for name_field in ['en_name', 'jp_name', 'zh_name']:
            name = concept.get(name_field, '').lower().strip()
            if name:
                name_to_id[name] = concept['concept_id']

    # Look for name mentions in definitions
    for concept in concepts:
        definition = concept.get('definition', '').lower()

        for name, target_id in name_to_id.items():
            if target_id == concept['concept_id']:
                continue  # Skip self-reference

            if len(name) > 3 and name in definition:
                # Check if relationship already exists
                rel_key = (concept['concept_id'], target_id)
                existing = any(
                    r['source'] == rel_key[0] and r['target'] == rel_key[1]
                    for r in relationships
                )
                if not existing:
                    relationships.append({
                        "source": concept['concept_id'],
                        "target": target_id,
                        "type": "reference",
                        "description": f"{concept.get('jp_name', concept.get('en_name', ''))}の定義が{name}に言及"
                    })

    return relationships

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    existing_db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    concepts_dir = base_dir / 'lbd-pipeline' / 'concepts'
    output_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'

    print("=== Concept Merge ===")
    print(f"Existing DB: {existing_db_path}")
    print(f"New concepts: {concepts_dir}")
    print()

    # Load existing database
    db = load_existing_db(existing_db_path)
    existing_concepts = db.get('concepts', [])
    existing_relationships = db.get('relationships', [])

    print(f"Existing concepts: {len(existing_concepts)}")
    print(f"Existing relationships: {len(existing_relationships)}")

    # Load new concepts
    new_concepts = load_new_concepts(concepts_dir)
    print(f"New concepts found: {len(new_concepts)}")

    if not new_concepts:
        print("No new concepts to merge. Exiting.")
        return

    # Merge and deduplicate
    all_concepts = existing_concepts + new_concepts
    merged_concepts = deduplicate_concepts(all_concepts)
    print(f"After deduplication: {len(merged_concepts)}")

    # Assign IDs to new concepts
    merged_concepts = assign_concept_ids(merged_concepts)

    # Detect new relationships
    new_relationships = detect_relationships(merged_concepts)

    # Merge relationships (avoid duplicates)
    existing_rel_keys = {(r['source'], r['target']) for r in existing_relationships}
    for rel in new_relationships:
        key = (rel['source'], rel['target'])
        if key not in existing_rel_keys:
            existing_relationships.append(rel)

    print(f"Total relationships: {len(existing_relationships)}")

    # Update database
    db['concepts'] = merged_concepts
    db['relationships'] = existing_relationships
    db['metadata']['last_updated'] = datetime.now().isoformat()
    db['metadata']['version'] = "2.0"

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print()
    print(f"Saved to: {output_path}")
    print(f"Total concepts: {len(merged_concepts)}")
    print(f"Total relationships: {len(existing_relationships)}")

if __name__ == '__main__':
    main()
