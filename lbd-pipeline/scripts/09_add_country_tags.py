#!/usr/bin/env python3
"""
09_add_country_tags.py - Add country tags to concepts in the database

This script:
1. Loads existing concepts from scs_concepts_db.json
2. Infers country_tag for each concept based on:
   - source_paper names
   - en_name/jp_name keywords
   - definition content
3. Outputs updated scs_concepts_db.json with country_tag field
4. Generates country_tag_report.json for review

Country Tags:
- CN: China (中国)
- JP: Japan (日本)
- US: United States (米国)
- EU: European Union (欧州)
- INTL: International/Comparative (国際/比較研究)
"""

import os
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Keywords for country inference
JAPAN_KEYWORDS = {
    'en_name': ['Japan', 'Japanese', 'JICC', 'CIC', 'KSC', 'Zengin', 'JBA'],
    'jp_name': ['日本', '全銀協', '信用情報機関', '個人信用情報', '暴力団', '反社'],
    'source_paper': ['Japan', '日本', 'NCS', 'METI', 'FSA', '金融庁', '経済産業省']
}

US_KEYWORDS = {
    'en_name': ['FICO', 'US', 'American', 'Experian', 'Equifax', 'TransUnion'],
    'jp_name': ['米国', 'アメリカ'],
    'source_paper': ['US', 'American', 'FICO', 'Fair Isaac']
}

EU_KEYWORDS = {
    'en_name': ['EU', 'GDPR', 'European', 'Brussels'],
    'jp_name': ['欧州', 'EU', '欧州連合'],
    'source_paper': ['EU', 'GDPR', 'European', 'CURIA', 'Brussels']
}

INTL_KEYWORDS = {
    'en_name': ['International', 'Global', 'Comparative', 'Cross-border'],
    'jp_name': ['国際', '比較', 'グローバル'],
    'source_paper': ['comparative', 'international', 'global']
}

def infer_country_tag(concept: dict, source_mapping: dict = None) -> tuple[str, str]:
    """
    Infer country tag for a concept.

    Returns:
        tuple: (country_tag, reason)
    """
    en_name = concept.get('en_name', '')
    jp_name = concept.get('jp_name', '')
    definition = concept.get('definition', '')
    source_papers = concept.get('source_papers', [])
    source_paper = concept.get('source_paper', '')

    # Combine source info
    all_sources = source_papers + ([source_paper] if source_paper else [])
    source_text = ' '.join(all_sources)

    # Check for Japan
    for field, keywords in JAPAN_KEYWORDS.items():
        text = locals().get(field, '') if field != 'source_paper' else source_text
        if isinstance(text, str):
            for kw in keywords:
                if kw.lower() in text.lower():
                    return 'JP', f'{field} contains "{kw}"'

    # Check for US
    for field, keywords in US_KEYWORDS.items():
        text = locals().get(field, '') if field != 'source_paper' else source_text
        if isinstance(text, str):
            for kw in keywords:
                if kw.lower() in text.lower():
                    return 'US', f'{field} contains "{kw}"'

    # Check for EU
    for field, keywords in EU_KEYWORDS.items():
        text = locals().get(field, '') if field != 'source_paper' else source_text
        if isinstance(text, str):
            for kw in keywords:
                if kw.lower() in text.lower():
                    return 'EU', f'{field} contains "{kw}"'

    # Check for International
    for field, keywords in INTL_KEYWORDS.items():
        text = locals().get(field, '') if field != 'source_paper' else source_text
        if isinstance(text, str):
            for kw in keywords:
                if kw.lower() in text.lower():
                    return 'INTL', f'{field} contains "{kw}"'

    # Default to China (most concepts are China-related)
    return 'CN', 'default (China SCS topic)'


def main():
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    output_dir = base_dir / 'lbd-output'

    print("=" * 60)
    print("Country Tag Addition Script")
    print("=" * 60)

    # Load database
    print(f"\nLoading database from: {db_path}")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    concepts = db.get('concepts', [])
    print(f"Found {len(concepts)} concepts")

    # Process concepts
    tag_stats = Counter()
    tag_details = []

    for concept in concepts:
        concept_id = concept.get('concept_id', 'unknown')
        en_name = concept.get('en_name', '')
        jp_name = concept.get('jp_name', '')

        # Skip if already has country_tag
        if 'country_tag' in concept:
            tag_stats[concept['country_tag']] += 1
            continue

        # Infer tag
        tag, reason = infer_country_tag(concept)
        concept['country_tag'] = tag
        tag_stats[tag] += 1

        tag_details.append({
            'concept_id': concept_id,
            'en_name': en_name,
            'jp_name': jp_name,
            'country_tag': tag,
            'reason': reason
        })

    # Update metadata
    db['metadata']['last_updated'] = datetime.now().isoformat()
    db['metadata']['country_tags_added'] = True

    # Save updated database
    print(f"\nSaving updated database to: {db_path}")
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_concepts': len(concepts),
        'tag_distribution': dict(tag_stats),
        'details': tag_details
    }

    report_path = output_dir / 'country_tag_report.json'
    print(f"Saving report to: {report_path}")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("Country Tag Distribution:")
    print("=" * 60)
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        tag_name = {
            'CN': 'China',
            'JP': 'Japan',
            'US': 'United States',
            'EU': 'European Union',
            'INTL': 'International'
        }.get(tag, tag)
        print(f"  {tag} ({tag_name}): {count} concepts")

    print(f"\nTotal: {len(concepts)} concepts tagged")
    print("=" * 60)


if __name__ == '__main__':
    main()
