#!/usr/bin/env python3
"""
06_run_predictions.py - Run predictions on all concepts

Applies trained models (or heuristics) to predict:
- Task A: Corporate impact classification
- Task B: 4-axis scores
- Task C: Transferability assessment
"""

import json
from pathlib import Path
from datetime import datetime

def load_concepts_db(db_path: Path) -> dict:
    """Load concepts database."""
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def predict_task_a(concept: dict) -> dict:
    """Predict corporate impact classification for a concept."""
    labels = []
    confidence = {}

    four_axis = concept.get('four_axis', [])
    definition = concept.get('definition', '').lower()
    concept_type = concept.get('concept_type', '')

    # Benefit predictions
    if any(kw in definition for kw in ['融資', '信用', 'ローン', '金融', 'loan', 'credit', 'finance']):
        labels.append('便益_金融アクセス')
        confidence['便益_金融アクセス'] = 0.85

    if any(kw in definition for kw in ['共有', '連携', '効率', 'sharing', 'integration']):
        labels.append('便益_取引コスト削減')
        confidence['便益_取引コスト削減'] = 0.75

    if any(kw in definition for kw in ['秩序', '取締', '違反', '不正', 'order', 'enforcement']):
        labels.append('便益_市場秩序')
        confidence['便益_市場秩序'] = 0.8

    # Cost predictions
    if any(kw in definition for kw in ['報告', '開示', '義務', '登録', 'disclosure', 'registration']):
        labels.append('コスト_コンプライアンス')
        confidence['コスト_コンプライアンス'] = 0.7

    if any(kw in definition for kw in ['参入', '障壁', 'barrier', 'entry']):
        labels.append('コスト_参入障壁')
        confidence['コスト_参入障壁'] = 0.65

    # Risk predictions
    if any(kw in definition for kw in ['連合懲戒', '連鎖', 'joint', 'punishment']):
        labels.append('リスク_連鎖制裁')
        confidence['リスク_連鎖制裁'] = 0.9

    if any(kw in definition for kw in ['恣意', '不透明', '基準', 'arbitrary']):
        labels.append('リスク_恣意的運用')
        confidence['リスク_恣意的運用'] = 0.7

    if any(kw in definition for kw in ['プライバシー', '個人情報', '監視', 'privacy', 'surveillance']):
        labels.append('リスク_プライバシー')
        confidence['リスク_プライバシー'] = 0.85

    if not labels:
        labels.append('便益_市場秩序')
        confidence['便益_市場秩序'] = 0.5

    return {
        "concept_id": concept.get('concept_id', ''),
        "jp_name": concept.get('jp_name', concept.get('en_name', '')),
        "labels": labels,
        "confidence": confidence,
        "primary_impact": labels[0] if labels else None
    }

def predict_task_b(concept: dict) -> dict:
    """Predict 4-axis scores for a concept."""
    four_axis = concept.get('four_axis', [])
    definition = concept.get('definition', '').lower()

    # Base scores from explicit four_axis assignment
    scores = {
        "governance": 0.8 if 'ガバナンス' in four_axis else 0.2,
        "data_flow": 0.8 if 'データフロー' in four_axis else 0.2,
        "incentive": 0.8 if 'インセンティブ設計' in four_axis else 0.2,
        "public_private": 0.8 if '官民関係' in four_axis else 0.2
    }

    # Adjust based on definition keywords
    governance_keywords = ['規制', '監督', '法', '政策', 'regulation', 'supervision', 'policy', 'law']
    data_keywords = ['情報', 'データ', '共有', 'プラットフォーム', 'data', 'information', 'platform', 'sharing']
    incentive_keywords = ['報酬', '罰則', '懲戒', '制裁', '制限', 'reward', 'punishment', 'sanction', 'restriction']
    public_private_keywords = ['民間', '企業', '官民', '公私', 'private', 'public', 'company', 'corporation']

    for kw in governance_keywords:
        if kw in definition:
            scores['governance'] = min(1.0, scores['governance'] + 0.1)

    for kw in data_keywords:
        if kw in definition:
            scores['data_flow'] = min(1.0, scores['data_flow'] + 0.1)

    for kw in incentive_keywords:
        if kw in definition:
            scores['incentive'] = min(1.0, scores['incentive'] + 0.1)

    for kw in public_private_keywords:
        if kw in definition:
            scores['public_private'] = min(1.0, scores['public_private'] + 0.1)

    # Round scores
    scores = {k: round(v, 2) for k, v in scores.items()}

    # Determine dominant axis
    dominant_axis = max(scores, key=scores.get)

    return {
        "concept_id": concept.get('concept_id', ''),
        "jp_name": concept.get('jp_name', concept.get('en_name', '')),
        "scores": scores,
        "dominant_axis": dominant_axis
    }

def predict_task_c(concept: dict) -> dict:
    """Predict transferability assessment for a concept."""
    four_axis = concept.get('four_axis', [])
    definition = concept.get('definition', '').lower()

    # Transferability factors
    transparency = 0.5
    relief_mechanism = 0.5
    proportionality = 0.5

    # Increase transparency score
    if any(kw in definition for kw in ['公開', '透明', '開示', 'disclosure', 'transparent', 'public']):
        transparency += 0.3

    # Relief mechanism presence
    if any(kw in definition for kw in ['修復', '救済', '訂正', '回復', 'repair', 'relief', 'correction']):
        relief_mechanism += 0.4

    # Decrease if harsh punitive measures
    if any(kw in definition for kw in ['連合懲戒', '禁止', '制限', '連鎖', 'joint punishment', 'ban', 'restriction']):
        proportionality -= 0.3
        transparency -= 0.2

    # Calculate overall transferability
    transferability_score = (transparency + relief_mechanism + proportionality) / 3

    if transferability_score > 0.6:
        recommendation = "移転推奨"
        reasoning = "透明性・救済メカニズムを備え、日本の法的枠組みと整合性が高い"
    elif transferability_score > 0.4:
        recommendation = "条件付き移転可能"
        reasoning = "一部修正を加えることで日本への適用が可能"
    else:
        recommendation = "移転非推奨"
        reasoning = "透明性・比例性の観点から日本の法的枠組みとの適合性が低い"

    return {
        "concept_id": concept.get('concept_id', ''),
        "jp_name": concept.get('jp_name', concept.get('en_name', '')),
        "transferability_score": round(transferability_score, 2),
        "transparency_score": round(transparency, 2),
        "relief_score": round(relief_mechanism, 2),
        "proportionality_score": round(proportionality, 2),
        "recommendation": recommendation,
        "reasoning": reasoning
    }

def main():
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    predictions_dir = base_dir / 'lbd-output' / 'predictions'
    predictions_dir.mkdir(exist_ok=True)

    print("=== Prediction Runner ===")
    print(f"Input: {db_path}")
    print()

    # Load database
    db = load_concepts_db(db_path)
    concepts = db.get('concepts', [])
    print(f"Running predictions on {len(concepts)} concepts")

    # Task A predictions
    task_a_results = [predict_task_a(c) for c in concepts]
    task_a_path = predictions_dir / 'corporate_impact.json'
    with open(task_a_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "task": "A - Corporate Impact Classification",
                "concept_count": len(task_a_results),
                "created_at": datetime.now().isoformat()
            },
            "predictions": task_a_results
        }, f, ensure_ascii=False, indent=2)
    print(f"Task A: {len(task_a_results)} predictions -> {task_a_path}")

    # Task B predictions
    task_b_results = [predict_task_b(c) for c in concepts]
    task_b_path = predictions_dir / 'four_axis_scores.json'
    with open(task_b_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "task": "B - 4-Axis Score Regression",
                "concept_count": len(task_b_results),
                "created_at": datetime.now().isoformat()
            },
            "predictions": task_b_results
        }, f, ensure_ascii=False, indent=2)
    print(f"Task B: {len(task_b_results)} predictions -> {task_b_path}")

    # Task C predictions
    task_c_results = [predict_task_c(c) for c in concepts]
    task_c_path = predictions_dir / 'transferability.json'
    with open(task_c_path, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "task": "C - Institutional Transferability",
                "concept_count": len(task_c_results),
                "created_at": datetime.now().isoformat()
            },
            "predictions": task_c_results
        }, f, ensure_ascii=False, indent=2)
    print(f"Task C: {len(task_c_results)} predictions -> {task_c_path}")

    # Summary statistics
    print()
    print("=== Summary ===")

    # Task A summary
    impact_counts = {}
    for result in task_a_results:
        for label in result['labels']:
            impact_counts[label] = impact_counts.get(label, 0) + 1
    print("Task A - Impact Distribution:")
    for label, count in sorted(impact_counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {count}")

    # Task B summary
    dominant_counts = {}
    for result in task_b_results:
        axis = result['dominant_axis']
        dominant_counts[axis] = dominant_counts.get(axis, 0) + 1
    print("\nTask B - Dominant Axis Distribution:")
    for axis, count in sorted(dominant_counts.items(), key=lambda x: -x[1]):
        print(f"  {axis}: {count}")

    # Task C summary
    rec_counts = {}
    for result in task_c_results:
        rec = result['recommendation']
        rec_counts[rec] = rec_counts.get(rec, 0) + 1
    print("\nTask C - Transferability Recommendation:")
    for rec, count in sorted(rec_counts.items(), key=lambda x: -x[1]):
        print(f"  {rec}: {count}")

if __name__ == '__main__':
    main()
