#!/usr/bin/env python3
"""
02_chunk_texts.py - Split extracted texts into chunks for processing

Creates chunks of ~3000 characters, respecting paragraph boundaries.
Output: chunks/{source_id}/chunk_{index}.json
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

# Configuration
CHUNK_SIZE = 3000  # Target characters per chunk
MIN_CHUNK_SIZE = 500  # Minimum chunk size to avoid tiny fragments
OVERLAP = 200  # Character overlap between chunks for context

def sanitize_source_id(filename: str) -> str:
    """Convert filename to a valid source ID."""
    # Remove extension and sanitize
    name = Path(filename).stem
    # Replace problematic characters
    name = re.sub(r'[^\w\-]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    # Trim to reasonable length
    return name[:80].strip('_')

def split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs."""
    # Split on double newlines or multiple whitespace lines
    paragraphs = re.split(r'\n\s*\n', text)
    # Filter empty paragraphs
    return [p.strip() for p in paragraphs if p.strip()]

def create_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[dict]:
    """
    Split text into chunks of approximately chunk_size characters.
    Respects paragraph boundaries where possible.
    """
    paragraphs = split_into_paragraphs(text)
    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_size = len(para)

        # If single paragraph exceeds chunk size, split it
        if para_size > chunk_size:
            # First, save current chunk if non-empty
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            # Split large paragraph by sentences or fixed size
            sentences = re.split(r'(?<=[.!?。！？])\s+', para)
            temp_chunk = []
            temp_size = 0

            for sent in sentences:
                if temp_size + len(sent) > chunk_size and temp_chunk:
                    chunks.append(' '.join(temp_chunk))
                    temp_chunk = []
                    temp_size = 0
                temp_chunk.append(sent)
                temp_size += len(sent)

            if temp_chunk:
                chunks.append(' '.join(temp_chunk))

        # If adding paragraph exceeds chunk size, start new chunk
        elif current_size + para_size > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size

        else:
            current_chunk.append(para)
            current_size += para_size

    # Don't forget the last chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    # Filter out tiny chunks (merge with previous if possible)
    filtered_chunks = []
    for chunk in chunks:
        if len(chunk) < MIN_CHUNK_SIZE and filtered_chunks:
            # Merge with previous chunk
            filtered_chunks[-1] = filtered_chunks[-1] + '\n\n' + chunk
        else:
            filtered_chunks.append(chunk)

    # Create chunk objects with metadata
    chunk_objects = []
    for i, chunk_text in enumerate(filtered_chunks):
        chunk_objects.append({
            'chunk_index': i,
            'char_count': len(chunk_text),
            'text': chunk_text
        })

    return chunk_objects

def process_all_texts(extracted_dir: Path, chunks_dir: Path) -> dict:
    """Process all extracted text files and create chunks."""
    stats = {
        'total_sources': 0,
        'total_chunks': 0,
        'total_chars': 0,
        'sources': []
    }

    # Get all text files
    txt_files = sorted(extracted_dir.glob('*.txt'))

    print(f"Found {len(txt_files)} text files")
    print()

    for txt_file in txt_files:
        source_id = sanitize_source_id(txt_file.name)

        # Read text
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        char_count = len(text)

        # Skip very small files (likely failed extractions)
        if char_count < 100:
            print(f"[SKIP] {source_id}: too small ({char_count} chars)")
            continue

        # Create chunks
        chunks = create_chunks(text)

        # Create output directory for this source
        source_dir = chunks_dir / source_id
        source_dir.mkdir(parents=True, exist_ok=True)

        # Save each chunk
        for chunk in chunks:
            chunk_file = source_dir / f"chunk_{chunk['chunk_index']:04d}.json"
            chunk_data = {
                'source_id': source_id,
                'source_file': txt_file.name,
                **chunk
            }
            with open(chunk_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)

        # Update stats
        stats['total_sources'] += 1
        stats['total_chunks'] += len(chunks)
        stats['total_chars'] += char_count
        stats['sources'].append({
            'source_id': source_id,
            'original_file': txt_file.name,
            'char_count': char_count,
            'chunk_count': len(chunks)
        })

        print(f"[OK] {source_id}: {char_count:,} chars -> {len(chunks)} chunks")

    return stats

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent
    extracted_dir = base_dir / 'lbd-pipeline' / 'extracted'
    chunks_dir = base_dir / 'lbd-pipeline' / 'chunks'

    print("=== Text Chunking ===")
    print(f"Source: {extracted_dir}")
    print(f"Output: {chunks_dir}")
    print(f"Chunk size: ~{CHUNK_SIZE} chars")
    print()

    # Process all texts
    stats = process_all_texts(extracted_dir, chunks_dir)

    # Save stats
    stats['created_at'] = datetime.now().isoformat()
    stats['chunk_size_target'] = CHUNK_SIZE

    stats_file = chunks_dir / 'chunk_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print()
    print("=== Summary ===")
    print(f"Sources processed: {stats['total_sources']}")
    print(f"Total chunks created: {stats['total_chunks']}")
    print(f"Total characters: {stats['total_chars']:,}")
    print(f"Average chunks/source: {stats['total_chunks'] / max(1, stats['total_sources']):.1f}")
    print()
    print(f"Stats saved to: {stats_file}")

if __name__ == '__main__':
    main()
