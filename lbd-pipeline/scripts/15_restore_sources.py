#!/usr/bin/env python3
"""
15_restore_sources.py - Restore source_papers from extraction files

This script:
1. Scans all extraction files in concepts/ directory
2. Builds a mapping of concept names to source_ids
3. Updates scs_concepts_db.json with missing source_papers
"""

import json
from pathlib import Path
from datetime import datetime


def load_extraction_files(concepts_dir: Path) -> dict:
    """
    Load all extraction files and build concept name -> source_id mapping.
    Returns dict: {(jp_name, en_name): [source_ids]}
    """
    concept_sources = {}

    for source_dir in sorted(concepts_dir.iterdir()):
        if not source_dir.is_dir():
            continue

        # Process all JSON files in the directory
        for json_file in source_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                source_id = data.get('source_id', source_dir.name)
                concepts = data.get('concepts', [])

                for concept in concepts:
                    jp_name = concept.get('jp_name', '').strip()
                    en_name = concept.get('en_name', '').strip().lower()

                    if jp_name or en_name:
                        key = (jp_name, en_name)
                        if key not in concept_sources:
                            concept_sources[key] = set()
                        concept_sources[key].add(source_id)

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not parse {json_file}: {e}")

    return concept_sources


def restore_sources(db: dict, concept_sources: dict) -> int:
    """
    Update source_papers for concepts that have empty sources.
    Returns count of updated concepts.
    """
    updated_count = 0

    for concept in db.get('concepts', []):
        # Skip if already has sources
        if concept.get('source_papers') and len(concept['source_papers']) > 0:
            continue

        jp_name = concept.get('jp_name', '').strip()
        en_name = concept.get('en_name', '').strip().lower()

        # Try to find matching source
        key = (jp_name, en_name)
        if key in concept_sources:
            concept['source_papers'] = list(concept_sources[key])
            updated_count += 1
            continue

        # Try partial matches (jp_name only)
        for (stored_jp, stored_en), sources in concept_sources.items():
            if jp_name and stored_jp == jp_name:
                concept['source_papers'] = list(sources)
                updated_count += 1
                break
            elif en_name and stored_en == en_name:
                concept['source_papers'] = list(sources)
                updated_count += 1
                break

    return updated_count


def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    concepts_dir = base_dir / 'lbd-pipeline' / 'concepts'
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'

    print("=" * 60)
    print("Restore Source Papers")
    print("=" * 60)
    print(f"Concepts directory: {concepts_dir}")
    print(f"Database: {db_path}")
    print()

    # Load extraction files
    print("Loading extraction files...")
    concept_sources = load_extraction_files(concepts_dir)
    print(f"Found {len(concept_sources)} unique concept name pairs")
    print()

    # Load database
    print("Loading database...")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    total_concepts = len(db.get('concepts', []))
    empty_before = sum(1 for c in db['concepts'] if not c.get('source_papers'))
    print(f"Total concepts: {total_concepts}")
    print(f"Concepts without sources: {empty_before}")
    print()

    # Restore sources
    print("Restoring source_papers...")
    updated_count = restore_sources(db, concept_sources)

    empty_after = sum(1 for c in db['concepts'] if not c.get('source_papers'))

    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Updated: {updated_count} concepts")
    print(f"Empty before: {empty_before}")
    print(f"Empty after: {empty_after}")
    print(f"Remaining empty: {empty_after} ({empty_after/total_concepts*100:.1f}%)")

    if updated_count > 0:
        # Update metadata
        db['metadata']['last_updated'] = datetime.now().isoformat()
        db['metadata']['source_restoration'] = {
            'timestamp': datetime.now().isoformat(),
            'updated_count': updated_count,
            'remaining_empty': empty_after
        }

        # Save
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        print(f"\nSaved to: {db_path}")
    else:
        print("\nNo updates needed.")


if __name__ == '__main__':
    main()
