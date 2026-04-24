#!/usr/bin/env python3
"""
13_infer_hierarchy.py - Infer is-a (hierarchical) relationships between concepts

Based on Fukuda et al. (2024) methodology:
1. Compute embeddings using Sentence-BERT
2. Find candidate pairs with moderate cosine similarity (0.50-0.80)
3. Classify relationship type: A is-a B, B is-a A, or no relation

This script addresses the problem of isolated concepts (220+ with no relationships)
by inferring subsumption (is-a) relationships.

Output:
- inferred_relationships.json: List of inferred is-a relationships
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Check if sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    print("Warning: sentence-transformers not installed.")
    print("Install with: pip install sentence-transformers scikit-learn")


def compute_embeddings(concepts: list, model_name: str = 'paraphrase-multilingual-mpnet-base-v2') -> np.ndarray:
    """Compute embeddings using Sentence-BERT."""
    print(f"Loading Sentence-BERT model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = []
    for c in concepts:
        jp_name = c.get('jp_name', '')
        en_name = c.get('en_name', '')
        definition = c.get('definition', '')
        combined = f"{jp_name} {en_name} {definition}".strip()
        texts.append(combined if combined else "unknown")

    print(f"Computing embeddings for {len(texts)} concepts...")
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings


def find_hierarchy_candidates(concepts: list, embeddings: np.ndarray,
                               min_threshold: float = 0.50,
                               max_threshold: float = 0.80,
                               max_candidates: int = 500) -> list:
    """
    Find candidate pairs for is-a relationship inference.

    We look for pairs with moderate similarity (0.50-0.80):
    - Too high (>0.80): likely synonyms, not hierarchy
    - Too low (<0.50): likely unrelated
    - Moderate (0.50-0.80): potential hierarchical relationship

    Args:
        concepts: List of concept dictionaries
        embeddings: Numpy array of embeddings
        min_threshold: Minimum cosine similarity
        max_threshold: Maximum cosine similarity (to exclude synonyms)
        max_candidates: Maximum number of candidates to return

    Returns:
        List of (idx_a, idx_b, similarity) tuples
    """
    print(f"Computing cosine similarity matrix...")
    sim_matrix = cosine_similarity(embeddings)

    pairs = []
    n = len(concepts)
    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i][j]
            if min_threshold <= sim < max_threshold:
                pairs.append((i, j, float(sim)))

    # Sort by similarity (descending)
    pairs.sort(key=lambda x: -x[2])

    # Limit to max_candidates
    pairs = pairs[:max_candidates]

    print(f"Found {len(pairs)} hierarchy candidates (similarity {min_threshold}-{max_threshold})")
    return pairs


def infer_hierarchy_heuristic(concept_a: dict, concept_b: dict) -> dict:
    """
    Infer is-a relationship using heuristics.

    Heuristics:
    1. If A's name is contained in B's name → B is-a A (B is more specific)
    2. If A's definition mentions B's name → A is-a B
    3. If A has more source_papers → A is likely more general
    4. Compare concept types (theory > mechanism > policy/data_system)

    Returns:
        dict with 'relation', 'confidence', 'reasoning'
    """
    a_jp = concept_a.get('jp_name', '')
    a_en = concept_a.get('en_name', '')
    a_def = concept_a.get('definition', '')
    a_type = concept_a.get('concept_type', '')
    a_sources = len(concept_a.get('source_papers', []))

    b_jp = concept_b.get('jp_name', '')
    b_en = concept_b.get('en_name', '')
    b_def = concept_b.get('definition', '')
    b_type = concept_b.get('concept_type', '')
    b_sources = len(concept_b.get('source_papers', []))

    relation = 'no_relation'
    confidence = 0.0
    reasoning = []

    # Type hierarchy: theory > mechanism > policy/data_system > actor > phenomenon
    type_rank = {
        'theory': 5,
        'mechanism': 4,
        'policy': 3,
        'data_system': 3,
        'actor': 2,
        'phenomenon': 1
    }

    a_rank = type_rank.get(a_type, 0)
    b_rank = type_rank.get(b_type, 0)

    # Heuristic 1: Name containment
    a_names = {a_jp.lower(), a_en.lower()} - {''}
    b_names = {b_jp.lower(), b_en.lower()} - {''}

    for a_name in a_names:
        for b_name in b_names:
            if len(a_name) > 3 and a_name in b_name and a_name != b_name:
                # B contains A's name → B is more specific → B is-a A
                relation = 'B_is_a_A'
                confidence = 0.7
                reasoning.append(f"B's name contains A's name: '{b_name}' contains '{a_name}'")
                break
            if len(b_name) > 3 and b_name in a_name and a_name != b_name:
                # A contains B's name → A is more specific → A is-a B
                relation = 'A_is_a_B'
                confidence = 0.7
                reasoning.append(f"A's name contains B's name: '{a_name}' contains '{b_name}'")
                break

    # Heuristic 2: Definition mentions
    if relation == 'no_relation':
        for b_name in b_names:
            if len(b_name) > 3 and b_name in a_def.lower():
                # A's definition mentions B → A is-a B
                relation = 'A_is_a_B'
                confidence = 0.6
                reasoning.append(f"A's definition mentions B: '{b_name}'")
                break

        for a_name in a_names:
            if len(a_name) > 3 and a_name in b_def.lower():
                # B's definition mentions A → B is-a A
                if relation == 'no_relation':
                    relation = 'B_is_a_A'
                    confidence = 0.6
                    reasoning.append(f"B's definition mentions A: '{a_name}'")
                    break

    # Heuristic 3: Type hierarchy
    if relation == 'no_relation' and a_rank != b_rank:
        if a_rank > b_rank:
            # A is more abstract type → B is-a A
            relation = 'B_is_a_A'
            confidence = 0.4
            reasoning.append(f"Type hierarchy: {a_type}({a_rank}) > {b_type}({b_rank})")
        else:
            # B is more abstract type → A is-a B
            relation = 'A_is_a_B'
            confidence = 0.4
            reasoning.append(f"Type hierarchy: {b_type}({b_rank}) > {a_type}({a_rank})")

    # Heuristic 4: Source count (more sources = more general/fundamental)
    if relation == 'no_relation' and abs(a_sources - b_sources) >= 2:
        if a_sources > b_sources:
            # A has more sources → A is more fundamental → B is-a A
            relation = 'B_is_a_A'
            confidence = 0.3
            reasoning.append(f"Source count: A({a_sources}) > B({b_sources})")
        else:
            relation = 'A_is_a_B'
            confidence = 0.3
            reasoning.append(f"Source count: B({b_sources}) > A({a_sources})")

    return {
        'relation': relation,
        'confidence': confidence,
        'reasoning': '; '.join(reasoning) if reasoning else 'No clear hierarchical relationship'
    }


def get_isolated_concept_ids(concepts: list, relationships: list) -> set:
    """Find concept IDs that have no relationships."""
    connected = set()
    for rel in relationships:
        connected.add(rel.get('source', ''))
        connected.add(rel.get('target', ''))

    all_ids = {c['concept_id'] for c in concepts}
    isolated = all_ids - connected

    return isolated


def main():
    # Setup paths
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    output_dir = base_dir / 'lbd-output'

    print("=" * 60)
    print("Hierarchy Inference Script (Fukuda Method)")
    print("=" * 60)

    # Load database
    print(f"\nLoading database from: {db_path}")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    concepts = db.get('concepts', [])
    existing_relationships = db.get('relationships', [])

    print(f"Found {len(concepts)} concepts")
    print(f"Existing relationships: {len(existing_relationships)}")

    # Find isolated concepts
    isolated_ids = get_isolated_concept_ids(concepts, existing_relationships)
    print(f"Isolated concepts (no relationships): {len(isolated_ids)}")

    if not SBERT_AVAILABLE:
        print("\nERROR: sentence-transformers not available.")
        print("Please install with: pip install sentence-transformers scikit-learn")
        return

    # Compute embeddings
    embeddings = compute_embeddings(concepts)

    # Find hierarchy candidates
    # Focus on isolated concepts by giving them priority
    candidates = find_hierarchy_candidates(
        concepts, embeddings,
        min_threshold=0.50,
        max_threshold=0.85,  # Slightly higher to catch more candidates
        max_candidates=1000
    )

    # Create concept lookup
    concept_lookup = {c['concept_id']: c for c in concepts}
    id_to_idx = {c['concept_id']: i for i, c in enumerate(concepts)}

    # Prioritize pairs involving isolated concepts
    prioritized = []
    other = []

    for idx_a, idx_b, sim in candidates:
        c_a = concepts[idx_a]
        c_b = concepts[idx_b]

        if c_a['concept_id'] in isolated_ids or c_b['concept_id'] in isolated_ids:
            prioritized.append((idx_a, idx_b, sim))
        else:
            other.append((idx_a, idx_b, sim))

    # Process prioritized first, then others
    all_candidates = prioritized[:400] + other[:100]

    print(f"\nProcessing {len(all_candidates)} candidates...")
    print(f"  Involving isolated concepts: {len(prioritized[:400])}")
    print(f"  Other pairs: {len(other[:100])}")

    # Infer hierarchies
    inferred = []
    for idx_a, idx_b, cos_sim in all_candidates:
        c_a = concepts[idx_a]
        c_b = concepts[idx_b]

        result = infer_hierarchy_heuristic(c_a, c_b)

        if result['relation'] != 'no_relation' and result['confidence'] >= 0.3:
            # Determine source and target based on relation
            if result['relation'] == 'A_is_a_B':
                source_id = c_a['concept_id']
                target_id = c_b['concept_id']
            else:  # B_is_a_A
                source_id = c_b['concept_id']
                target_id = c_a['concept_id']

            inferred.append({
                'source': source_id,
                'target': target_id,
                'type': 'subsumption',
                'description': f'{concept_lookup[source_id].get("jp_name", "")} is-a {concept_lookup[target_id].get("jp_name", "")}',
                'similarity': {
                    'embedding_cos': round(cos_sim, 4),
                    'heuristic_confidence': result['confidence']
                },
                'reasoning': result['reasoning'],
                'inferred': True
            })

    print(f"\nInferred {len(inferred)} is-a relationships")

    # Count how many isolated concepts are now connected
    newly_connected = set()
    for rel in inferred:
        newly_connected.add(rel['source'])
        newly_connected.add(rel['target'])

    isolated_now_connected = isolated_ids & newly_connected
    print(f"Isolated concepts now connected: {len(isolated_now_connected)}/{len(isolated_ids)}")

    # Group by confidence
    high_conf = [r for r in inferred if r['similarity']['heuristic_confidence'] >= 0.6]
    medium_conf = [r for r in inferred if 0.4 <= r['similarity']['heuristic_confidence'] < 0.6]
    low_conf = [r for r in inferred if r['similarity']['heuristic_confidence'] < 0.4]

    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_concepts': len(concepts),
        'existing_relationships': len(existing_relationships),
        'isolated_concepts_before': len(isolated_ids),
        'inferred_relationships': len(inferred),
        'isolated_concepts_connected': len(isolated_now_connected),
        'statistics': {
            'high_confidence': len(high_conf),
            'medium_confidence': len(medium_conf),
            'low_confidence': len(low_conf)
        },
        'relationships': inferred
    }

    # Save report
    output_path = output_dir / 'inferred_relationships.json'
    print(f"\nSaving report to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print top inferred relationships
    print("\n" + "=" * 60)
    print("Top Inferred Relationships")
    print("=" * 60)

    for i, rel in enumerate(inferred[:20], 1):
        source = concept_lookup.get(rel['source'], {})
        target = concept_lookup.get(rel['target'], {})
        conf = rel['similarity']['heuristic_confidence']

        print(f"\n{i}. [{conf:.2f}] {source.get('jp_name', '')} is-a {target.get('jp_name', '')}")
        print(f"   ({source.get('en_name', '')} → {target.get('en_name', '')})")
        print(f"   Reasoning: {rel['reasoning'][:80]}...")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total concepts: {len(concepts)}")
    print(f"  Existing relationships: {len(existing_relationships)}")
    print(f"  Isolated before: {len(isolated_ids)}")
    print(f"  Inferred relationships: {len(inferred)}")
    print(f"    High confidence (>=0.6): {len(high_conf)}")
    print(f"    Medium confidence (0.4-0.6): {len(medium_conf)}")
    print(f"    Low confidence (<0.4): {len(low_conf)}")
    print(f"  Isolated now connected: {len(isolated_now_connected)}")
    print(f"  Remaining isolated: {len(isolated_ids) - len(isolated_now_connected)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
