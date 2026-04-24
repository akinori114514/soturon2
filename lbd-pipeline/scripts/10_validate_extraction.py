#!/usr/bin/env python3
"""
10_validate_extraction.py - Validate concept extraction coverage

This script:
1. Compares chunks processed vs concepts extracted per source
2. Identifies low-density sources (potential extraction gaps)
3. Identifies isolated concepts (no relationships)
4. Generates validation report

Output:
- coverage_report.json: Detailed statistics per source
- validation_report.md: Human-readable summary
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_db(db_path: Path) -> dict:
    """Load concepts database."""
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_chunks(chunks_dir: Path) -> dict:
    """Count chunks per source."""
    chunk_counts = {}
    for source_dir in chunks_dir.iterdir():
        if source_dir.is_dir():
            chunk_files = list(source_dir.glob('chunk_*.json'))
            chunk_counts[source_dir.name] = len(chunk_files)
    return chunk_counts

def count_concepts_per_source(db: dict) -> dict:
    """Count concepts per source paper."""
    source_counts = defaultdict(int)
    for concept in db.get('concepts', []):
        source_papers = concept.get('source_papers', [])
        source_paper = concept.get('source_paper', '')

        for sp in source_papers:
            source_counts[sp] += 1
        if source_paper:
            source_counts[source_paper] += 1

    return dict(source_counts)

def find_isolated_concepts(db: dict) -> list:
    """Find concepts with no relationships."""
    concepts = {c['concept_id']: c for c in db.get('concepts', [])}
    relationships = db.get('relationships', [])

    # Build set of connected concepts
    connected = set()
    for rel in relationships:
        connected.add(rel['source'])
        connected.add(rel['target'])

    # Also check related_concepts field
    for concept in concepts.values():
        related = concept.get('related_concepts', [])
        if related:
            connected.add(concept['concept_id'])
            connected.update(related)

    # Find isolated concepts
    isolated = []
    for concept_id, concept in concepts.items():
        if concept_id not in connected:
            isolated.append({
                'concept_id': concept_id,
                'jp_name': concept.get('jp_name', ''),
                'en_name': concept.get('en_name', ''),
                'source_papers': concept.get('source_papers', [])
            })

    return isolated

def calculate_density(chunk_count: int, concept_count: int) -> float:
    """Calculate concepts per chunk density."""
    if chunk_count == 0:
        return 0.0
    return concept_count / chunk_count

def main():
    # Setup paths
    base_dir = Path(__file__).parent.parent.parent
    chunks_dir = base_dir / 'lbd-pipeline' / 'chunks'
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    output_dir = base_dir / 'lbd-output'

    print("=" * 60)
    print("Extraction Validation Script")
    print("=" * 60)

    # Load data
    print(f"\nLoading database from: {db_path}")
    db = load_db(db_path)

    print(f"Counting chunks in: {chunks_dir}")
    chunk_counts = count_chunks(chunks_dir)

    # Analyze
    concept_counts = count_concepts_per_source(db)
    isolated = find_isolated_concepts(db)

    # Build report
    source_stats = []
    for source_id, chunk_count in sorted(chunk_counts.items()):
        concept_count = concept_counts.get(source_id, 0)
        density = calculate_density(chunk_count, concept_count)

        status = 'OK'
        if chunk_count > 0 and concept_count == 0:
            status = 'NOT_PROCESSED'
        elif density < 0.1 and chunk_count > 5:
            status = 'LOW_DENSITY'
        elif density > 0:
            status = 'OK'
        else:
            status = 'UNKNOWN'

        source_stats.append({
            'source_id': source_id,
            'chunk_count': chunk_count,
            'concept_count': concept_count,
            'density': round(density, 3),
            'status': status
        })

    # Statistics
    total_chunks = sum(s['chunk_count'] for s in source_stats)
    total_concepts = len(db.get('concepts', []))
    processed_sources = len([s for s in source_stats if s['concept_count'] > 0])
    not_processed = [s for s in source_stats if s['status'] == 'NOT_PROCESSED']
    low_density = [s for s in source_stats if s['status'] == 'LOW_DENSITY']

    # Country distribution
    country_dist = defaultdict(int)
    for concept in db.get('concepts', []):
        tag = concept.get('country_tag', 'CN')
        country_dist[tag] += 1

    # Generate JSON report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_sources': len(chunk_counts),
            'processed_sources': processed_sources,
            'total_chunks': total_chunks,
            'total_concepts': total_concepts,
            'total_relationships': len(db.get('relationships', [])),
            'isolated_concepts': len(isolated),
            'average_density': round(total_concepts / total_chunks if total_chunks > 0 else 0, 3)
        },
        'country_distribution': dict(country_dist),
        'sources': source_stats,
        'not_processed': not_processed,
        'low_density': low_density,
        'isolated_concepts': isolated[:20]  # Top 20
    }

    # Save JSON report
    json_path = output_dir / 'coverage_report.json'
    print(f"\nSaving JSON report to: {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Generate markdown report
    md_content = f"""# Extraction Validation Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Sources | {len(chunk_counts)} |
| Processed Sources | {processed_sources} ({processed_sources/len(chunk_counts)*100:.1f}%) |
| Total Chunks | {total_chunks} |
| Total Concepts | {total_concepts} |
| Total Relationships | {len(db.get('relationships', []))} |
| Isolated Concepts | {len(isolated)} ({len(isolated)/total_concepts*100:.1f}%) |
| Average Density | {total_concepts/total_chunks if total_chunks > 0 else 0:.3f} concepts/chunk |

## Country Distribution

| Country | Count | Percentage |
|---------|-------|------------|
"""
    for tag, count in sorted(country_dist.items(), key=lambda x: -x[1]):
        name = {'CN': 'China', 'JP': 'Japan', 'US': 'United States', 'EU': 'European Union', 'INTL': 'International'}.get(tag, tag)
        md_content += f"| {tag} ({name}) | {count} | {count/total_concepts*100:.1f}% |\n"

    md_content += f"""
## Not Processed Sources ({len(not_processed)})

These sources have chunks but no extracted concepts:

| Source ID | Chunks |
|-----------|--------|
"""
    for s in not_processed[:20]:
        md_content += f"| {s['source_id']} | {s['chunk_count']} |\n"

    if len(not_processed) > 20:
        md_content += f"| ... | ({len(not_processed) - 20} more) |\n"

    md_content += f"""
## Low Density Sources ({len(low_density)})

Sources with density < 0.1 concepts/chunk:

| Source ID | Chunks | Concepts | Density |
|-----------|--------|----------|---------|
"""
    for s in sorted(low_density, key=lambda x: x['density']):
        md_content += f"| {s['source_id']} | {s['chunk_count']} | {s['concept_count']} | {s['density']:.3f} |\n"

    md_content += f"""
## Isolated Concepts ({len(isolated)})

Concepts with no relationships (showing first 20):

| Concept ID | Japanese Name | English Name |
|------------|---------------|--------------|
"""
    for c in isolated[:20]:
        md_content += f"| {c['concept_id']} | {c['jp_name']} | {c['en_name']} |\n"

    md_content += """
## Recommendations

1. **Process unprocessed sources**: {} sources have chunks but no concepts extracted.
2. **Re-extract low-density sources**: {} sources may have incomplete extraction.
3. **Review isolated concepts**: {} concepts have no relationships and may need connecting.
""".format(len(not_processed), len(low_density), len(isolated))

    # Save markdown report
    md_path = output_dir / 'validation_report.md'
    print(f"Saving markdown report to: {md_path}")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # Print summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"  Total sources: {len(chunk_counts)}")
    print(f"  Processed: {processed_sources} ({processed_sources/len(chunk_counts)*100:.1f}%)")
    print(f"  Not processed: {len(not_processed)}")
    print(f"  Low density: {len(low_density)}")
    print(f"  Total concepts: {total_concepts}")
    print(f"  Isolated concepts: {len(isolated)}")
    print("\nCountry Distribution:")
    for tag, count in sorted(country_dist.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
