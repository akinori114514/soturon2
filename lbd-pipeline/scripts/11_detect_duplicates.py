#!/usr/bin/env python3
"""
11_detect_duplicates.py - Detect potential duplicate concepts using Sentence-BERT

Based on Fukuda et al. (2024) methodology:
1. Compute embeddings using Sentence-BERT (multilingual model)
2. Find candidate pairs with cosine similarity >= threshold
3. (Optional) Verify with LLM for final judgment

Output:
- merge_candidates.json: List of potential duplicates with similarity scores
"""

import json
import re
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
    print("Warning: sentence-transformers not installed. Using fallback string-based method.")
    print("Install with: pip install sentence-transformers scikit-learn")


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def string_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity (0-1)."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = normalize_text(s1), normalize_text(s2)
    if s1 == s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    distance = levenshtein_distance(s1, s2)
    return 1 - (distance / max_len)


def compute_embeddings_sbert(concepts: list, model_name: str = 'paraphrase-multilingual-mpnet-base-v2') -> np.ndarray:
    """
    Compute embeddings using Sentence-BERT.

    Args:
        concepts: List of concept dictionaries
        model_name: Sentence-BERT model name (multilingual for JP/CN/EN support)

    Returns:
        numpy array of embeddings (n_concepts x embedding_dim)
    """
    print(f"Loading Sentence-BERT model: {model_name}")
    model = SentenceTransformer(model_name)

    # Combine name and definition for richer semantic representation
    texts = []
    for c in concepts:
        jp_name = c.get('jp_name', '')
        en_name = c.get('en_name', '')
        definition = c.get('definition', '')
        # Combine all available text
        combined = f"{jp_name} {en_name} {definition}".strip()
        texts.append(combined if combined else "unknown")

    print(f"Computing embeddings for {len(texts)} concepts...")
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings


def find_similar_pairs_sbert(concepts: list, embeddings: np.ndarray, threshold: float = 0.80) -> list:
    """
    Find pairs of concepts with cosine similarity above threshold.

    Based on Fukuda et al. (2024): cos similarity >= 0.80 for synonym candidates

    Args:
        concepts: List of concept dictionaries
        embeddings: Numpy array of embeddings
        threshold: Minimum cosine similarity (default 0.80 per Fukuda paper)

    Returns:
        List of (idx_a, idx_b, similarity) tuples
    """
    print(f"Computing cosine similarity matrix ({len(concepts)}x{len(concepts)})...")
    sim_matrix = cosine_similarity(embeddings)

    pairs = []
    n = len(concepts)
    for i in range(n):
        for j in range(i + 1, n):
            if sim_matrix[i][j] >= threshold:
                pairs.append((i, j, float(sim_matrix[i][j])))

    # Sort by similarity (descending)
    pairs.sort(key=lambda x: -x[2])

    print(f"Found {len(pairs)} pairs with similarity >= {threshold}")
    return pairs


def find_duplicates_fallback(concepts: list, threshold: float = 0.6) -> list:
    """
    Fallback method using string similarity (Levenshtein distance).
    Used when sentence-transformers is not available.
    """
    duplicates = []
    checked_pairs = set()

    for i, c1 in enumerate(concepts):
        id1 = c1['concept_id']

        for j, c2 in enumerate(concepts):
            id2 = c2['concept_id']

            if id1 >= id2:
                continue
            pair_key = (id1, id2)
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            # Calculate similarities
            en_sim = string_similarity(c1.get('en_name', ''), c2.get('en_name', ''))
            jp_sim = string_similarity(c1.get('jp_name', ''), c2.get('jp_name', ''))
            name_sim = max(en_sim, jp_sim)

            if name_sim < 0.4:
                continue

            def_sim = string_similarity(c1.get('definition', ''), c2.get('definition', ''))

            # Structural similarity
            struct_sim = 0.0
            if c1.get('concept_type') == c2.get('concept_type'):
                struct_sim += 0.4
            if c1.get('country_tag') == c2.get('country_tag'):
                struct_sim += 0.2
            axes1 = set(c1.get('four_axis', []))
            axes2 = set(c2.get('four_axis', []))
            if axes1 and axes2:
                axis_overlap = len(axes1 & axes2) / len(axes1 | axes2)
                struct_sim += 0.4 * axis_overlap

            # Weighted overall similarity
            overall = 0.5 * name_sim + 0.3 * def_sim + 0.2 * struct_sim

            if overall >= threshold:
                duplicates.append({
                    'concept_a': {
                        'id': id1,
                        'en_name': c1.get('en_name', ''),
                        'jp_name': c1.get('jp_name', ''),
                        'source_papers': c1.get('source_papers', [])
                    },
                    'concept_b': {
                        'id': id2,
                        'en_name': c2.get('en_name', ''),
                        'jp_name': c2.get('jp_name', ''),
                        'source_papers': c2.get('source_papers', [])
                    },
                    'similarity': {
                        'name': round(name_sim, 3),
                        'definition': round(def_sim, 3),
                        'structure': round(struct_sim, 3),
                        'overall': round(overall, 3),
                        'method': 'levenshtein'
                    },
                    'action': 'manual_review'
                })

    duplicates.sort(key=lambda x: -x['similarity']['overall'])
    return duplicates


def main():
    # Setup paths
    base_dir = Path(__file__).parent.parent.parent
    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    output_dir = base_dir / 'lbd-output'

    print("=" * 60)
    print("Duplicate Detection Script (Fukuda Method)")
    print("=" * 60)

    # Load database
    print(f"\nLoading database from: {db_path}")
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    concepts = db.get('concepts', [])
    print(f"Found {len(concepts)} concepts")

    duplicates = []

    if SBERT_AVAILABLE:
        print("\n--- Using Sentence-BERT Method (Fukuda et al. 2024) ---")

        # Compute embeddings
        embeddings = compute_embeddings_sbert(concepts)

        # Find similar pairs (threshold 0.80 per Fukuda paper)
        similar_pairs = find_similar_pairs_sbert(concepts, embeddings, threshold=0.80)

        # Also find moderately similar pairs for review (0.70-0.80)
        moderate_pairs = find_similar_pairs_sbert(concepts, embeddings, threshold=0.70)
        moderate_pairs = [(i, j, s) for (i, j, s) in moderate_pairs if s < 0.80]

        # Build duplicate candidates
        for idx_a, idx_b, cos_sim in similar_pairs:
            c1 = concepts[idx_a]
            c2 = concepts[idx_b]

            duplicates.append({
                'concept_a': {
                    'id': c1['concept_id'],
                    'en_name': c1.get('en_name', ''),
                    'jp_name': c1.get('jp_name', ''),
                    'definition': c1.get('definition', '')[:200],
                    'source_papers': c1.get('source_papers', [])
                },
                'concept_b': {
                    'id': c2['concept_id'],
                    'en_name': c2.get('en_name', ''),
                    'jp_name': c2.get('jp_name', ''),
                    'definition': c2.get('definition', '')[:200],
                    'source_papers': c2.get('source_papers', [])
                },
                'similarity': {
                    'embedding_cos': round(cos_sim, 4),
                    'method': 'sentence-bert',
                    'model': 'paraphrase-multilingual-mpnet-base-v2'
                },
                'confidence': 'high' if cos_sim >= 0.90 else 'medium',
                'action': 'merge' if cos_sim >= 0.90 else 'manual_review'
            })

        # Add moderate similarity pairs as low confidence
        for idx_a, idx_b, cos_sim in moderate_pairs[:50]:  # Limit to top 50
            c1 = concepts[idx_a]
            c2 = concepts[idx_b]

            duplicates.append({
                'concept_a': {
                    'id': c1['concept_id'],
                    'en_name': c1.get('en_name', ''),
                    'jp_name': c1.get('jp_name', ''),
                    'definition': c1.get('definition', '')[:200],
                    'source_papers': c1.get('source_papers', [])
                },
                'concept_b': {
                    'id': c2['concept_id'],
                    'en_name': c2.get('en_name', ''),
                    'jp_name': c2.get('jp_name', ''),
                    'definition': c2.get('definition', '')[:200],
                    'source_papers': c2.get('source_papers', [])
                },
                'similarity': {
                    'embedding_cos': round(cos_sim, 4),
                    'method': 'sentence-bert',
                    'model': 'paraphrase-multilingual-mpnet-base-v2'
                },
                'confidence': 'low',
                'action': 'manual_review'
            })

    else:
        print("\n--- Using Fallback Method (Levenshtein Distance) ---")
        duplicates = find_duplicates_fallback(concepts, threshold=0.6)

    print(f"\nFound {len(duplicates)} potential duplicates")

    # Count by confidence/action
    high_conf = len([d for d in duplicates if d.get('confidence') == 'high'])
    medium_conf = len([d for d in duplicates if d.get('confidence') == 'medium'])
    low_conf = len([d for d in duplicates if d.get('confidence') == 'low'])

    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_concepts': len(concepts),
        'duplicate_candidates': len(duplicates),
        'method': 'sentence-bert' if SBERT_AVAILABLE else 'levenshtein',
        'threshold': 0.80 if SBERT_AVAILABLE else 0.6,
        'statistics': {
            'high_confidence': high_conf,
            'medium_confidence': medium_conf,
            'low_confidence': low_conf
        },
        'merge_candidates': duplicates
    }

    # Save report
    output_path = output_dir / 'merge_candidates.json'
    print(f"\nSaving report to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print top candidates
    print("\n" + "=" * 60)
    print("Top Duplicate Candidates")
    print("=" * 60)

    for i, dup in enumerate(duplicates[:15], 1):
        sim = dup['similarity']
        if 'embedding_cos' in sim:
            score_str = f"cos={sim['embedding_cos']:.3f}"
        else:
            score_str = f"overall={sim.get('overall', 0):.3f}"

        conf = dup.get('confidence', 'unknown')
        action = dup.get('action', 'unknown')

        print(f"\n{i}. [{conf.upper()}] {score_str}")
        print(f"   A: {dup['concept_a']['en_name']} ({dup['concept_a']['jp_name']})")
        print(f"   B: {dup['concept_b']['en_name']} ({dup['concept_b']['jp_name']})")
        print(f"   Action: {action}")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total concepts: {len(concepts)}")
    print(f"  Duplicate candidates: {len(duplicates)}")
    print(f"    High confidence (merge): {high_conf}")
    print(f"    Medium confidence (review): {medium_conf}")
    print(f"    Low confidence (review): {low_conf}")
    print("=" * 60)


if __name__ == '__main__':
    main()
