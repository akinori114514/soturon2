#!/usr/bin/env python3
"""
05_generate_training_data.py - Generate training data for multi-task prediction

Creates training data for:
- Task A: Corporate impact classification (benefit/cost/risk)
- Task B: 4-axis score regression
- Task C: Institutional transferability prediction (inverse design)
"""

import json
from pathlib import Path
from datetime import datetime

def load_concepts_db(db_path: Path) -> dict:
    """Load concepts database."""
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_task_a_data(concepts: list) -> list:
    """
    Generate Task A training data: Corporate impact classification.

    Labels: 便益_取引コスト削減, 便益_金融アクセス, 便益_市場秩序,
            コスト_コンプライアンス, コスト_参入障壁,
            リスク_恣意的運用, リスク_連鎖制裁, リスク_プライバシー
    """
    training_data = []

    # Define label mapping based on concept type and four_axis
    for concept in concepts:
        labels = []
        confidence = {}

        concept_type = concept.get('concept_type', '')
        four_axis = concept.get('four_axis', [])
        definition = concept.get('definition', '')

        # Heuristic label assignment based on concept characteristics
        if 'インセンティブ設計' in four_axis:
            if any(keyword in definition for keyword in ['融資', '信用', 'ローン', '金融']):
                labels.append('便益_金融アクセス')
                confidence['便益_金融アクセス'] = 0.8
            if any(keyword in definition for keyword in ['懲戒', '罰則', '制裁', 'blacklist']):
                labels.append('リスク_連鎖制裁')
                confidence['リスク_連鎖制裁'] = 0.7

        if 'ガバナンス' in four_axis:
            if any(keyword in definition for keyword in ['秩序', '取締', '違反', '不正']):
                labels.append('便益_市場秩序')
                confidence['便益_市場秩序'] = 0.75
            if any(keyword in definition for keyword in ['規制', 'コンプライアンス', '報告', '義務']):
                labels.append('コスト_コンプライアンス')
                confidence['コスト_コンプライアンス'] = 0.6

        if 'データフロー' in four_axis:
            if any(keyword in definition for keyword in ['共有', '連携', '統合', 'データ']):
                labels.append('便益_取引コスト削減')
                confidence['便益_取引コスト削減'] = 0.7
            if any(keyword in definition for keyword in ['プライバシー', '個人情報', '監視']):
                labels.append('リスク_プライバシー')
                confidence['リスク_プライバシー'] = 0.8

        if concept_type == 'mechanism' and '制限' in definition:
            labels.append('リスク_恣意的運用')
            confidence['リスク_恣意的運用'] = 0.6

        if not labels:
            labels.append('便益_市場秩序')
            confidence['便益_市場秩序'] = 0.5

        # Create training example
        input_text = f"{concept.get('jp_name', concept.get('en_name', ''))}（{concept.get('en_name', '')}）: {definition}"

        training_data.append({
            "instruction": "以下のSCS制度要素が企業経営環境に与える影響を分類してください。",
            "input": input_text,
            "output": json.dumps({"labels": labels, "confidence": confidence}, ensure_ascii=False)
        })

    return training_data

def generate_task_b_data(concepts: list) -> list:
    """
    Generate Task B training data: 4-axis score regression.

    Scores: governance, data_flow, incentive, public_private (0.0-1.0)
    """
    training_data = []

    for concept in concepts:
        four_axis = concept.get('four_axis', [])
        definition = concept.get('definition', '')

        # Calculate scores based on presence in four_axis
        scores = {
            "governance": 0.8 if 'ガバナンス' in four_axis else 0.2,
            "data_flow": 0.8 if 'データフロー' in four_axis else 0.2,
            "incentive": 0.8 if 'インセンティブ設計' in four_axis else 0.2,
            "public_private": 0.8 if '官民関係' in four_axis else 0.2
        }

        # Adjust scores based on definition keywords
        if any(kw in definition for kw in ['規制', '監督', '法規', '立法']):
            scores['governance'] = min(1.0, scores['governance'] + 0.15)
        if any(kw in definition for kw in ['情報', 'データ', '共有', 'プラットフォーム']):
            scores['data_flow'] = min(1.0, scores['data_flow'] + 0.15)
        if any(kw in definition for kw in ['報酬', '罰則', '懲戒', '制裁']):
            scores['incentive'] = min(1.0, scores['incentive'] + 0.15)
        if any(kw in definition for kw in ['民間', '企業', '官民', '公私']):
            scores['public_private'] = min(1.0, scores['public_private'] + 0.15)

        input_text = f"{concept.get('jp_name', concept.get('en_name', ''))}（{concept.get('en_name', '')}）: {definition}"

        training_data.append({
            "instruction": "以下のSCS制度要素の4軸スコアを算出してください。",
            "input": input_text,
            "output": json.dumps(scores, ensure_ascii=False)
        })

    return training_data

def generate_task_c_data(concepts: list) -> list:
    """
    Generate Task C training data: Institutional transferability prediction (inverse design).

    Given target conditions, recommend suitable SCS institutional elements.
    """
    training_data = []

    # Define condition combinations and suitable concepts
    conditions = [
        {
            "透明性要件": "High",
            "救済メカニズム": "Full",
            "民間関与度": "Med",
            "データ連結度": "Partial",
            "制裁強度": "Soft"
        },
        {
            "透明性要件": "Med",
            "救済メカニズム": "Partial",
            "民間関与度": "High",
            "データ連結度": "Full",
            "制裁強度": "Med"
        },
        {
            "透明性要件": "Low",
            "救済メカニズム": "None",
            "民間関与度": "Low",
            "データ連結度": "Full",
            "制裁強度": "Hard"
        }
    ]

    # Map concepts to condition suitability
    for condition in conditions:
        recommended = []
        not_recommended = []

        for concept in concepts:
            four_axis = concept.get('four_axis', [])
            definition = concept.get('definition', '')
            jp_name = concept.get('jp_name', concept.get('en_name', ''))

            # High transparency + Full relief: favor repair/correction mechanisms
            if condition["透明性要件"] == "High" and condition["救済メカニズム"] == "Full":
                if any(kw in definition for kw in ['修復', '救済', '訂正', '回復']):
                    recommended.append(jp_name)
                elif any(kw in definition for kw in ['連合懲戒', '制限', 'blacklist']):
                    not_recommended.append(jp_name)

            # Low transparency + Hard sanctions: favor punitive mechanisms
            if condition["透明性要件"] == "Low" and condition["制裁強度"] == "Hard":
                if any(kw in definition for kw in ['懲戒', '制裁', '制限', '禁止']):
                    recommended.append(jp_name)
                elif any(kw in definition for kw in ['透明', '公開', '救済']):
                    not_recommended.append(jp_name)

            # High private involvement: favor private sector mechanisms
            if condition["民間関与度"] == "High":
                if '官民関係' in four_axis or any(kw in definition for kw in ['民間', '企業', 'Alibaba', 'Tencent']):
                    recommended.append(jp_name)

        # Remove duplicates
        recommended = list(set(recommended))[:5]
        not_recommended = list(set(not_recommended))[:3]

        if recommended:
            training_data.append({
                "instruction": "以下の条件を満たすSCS制度要素を推薦してください。",
                "input": json.dumps(condition, ensure_ascii=False),
                "output": json.dumps({
                    "recommended": recommended,
                    "not_recommended": not_recommended,
                    "reasoning": f"条件 透明性={condition['透明性要件']}, 救済={condition['救済メカニズム']}, 制裁={condition['制裁強度']} に基づき推薦。"
                }, ensure_ascii=False)
            })

    return training_data

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent

    db_path = base_dir / 'lbd-output' / 'scs_concepts_db.json'
    training_dir = base_dir / 'lbd-pipeline' / 'training_data'
    training_dir.mkdir(exist_ok=True)

    print("=== Training Data Generator ===")
    print(f"Input: {db_path}")
    print()

    # Load database
    db = load_concepts_db(db_path)
    concepts = db.get('concepts', [])
    print(f"Loaded {len(concepts)} concepts")

    # Generate Task A data
    task_a_data = generate_task_a_data(concepts)
    task_a_path = training_dir / 'task_a_classification.jsonl'
    with open(task_a_path, 'w', encoding='utf-8') as f:
        for item in task_a_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Task A: {len(task_a_data)} examples -> {task_a_path}")

    # Generate Task B data
    task_b_data = generate_task_b_data(concepts)
    task_b_path = training_dir / 'task_b_regression.jsonl'
    with open(task_b_path, 'w', encoding='utf-8') as f:
        for item in task_b_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Task B: {len(task_b_data)} examples -> {task_b_path}")

    # Generate Task C data
    task_c_data = generate_task_c_data(concepts)
    task_c_path = training_dir / 'task_c_inverse.jsonl'
    with open(task_c_path, 'w', encoding='utf-8') as f:
        for item in task_c_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Task C: {len(task_c_data)} examples -> {task_c_path}")

    print()
    print("Training data generation complete!")

if __name__ == '__main__':
    main()
