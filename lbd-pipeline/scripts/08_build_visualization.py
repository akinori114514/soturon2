#!/usr/bin/env python3
"""
08_build_visualization.py
Builds a standalone HTML visualization with embedded JSON data.
This allows the visualization to work when opened directly as a local file.
"""

import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "lbd-output"
VIS_DIR = OUTPUT_DIR / "visualization"

GRAPH_FILE = OUTPUT_DIR / "knowledge_graph.json"
GAP_FILE = OUTPUT_DIR / "gap_candidates.json"
TEMPLATE_FILE = VIS_DIR / "index.html"
OUTPUT_FILE = VIS_DIR / "index_standalone.html"


def main():
    print("=== Building Standalone Visualization ===")

    # Load JSON data
    print(f"Loading: {GRAPH_FILE}")
    with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

    print(f"Loading: {GAP_FILE}")
    with open(GAP_FILE, 'r', encoding='utf-8') as f:
        gap_data = json.load(f)

    # Read template HTML
    print(f"Reading template: {TEMPLATE_FILE}")
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Create embedded data script
    embedded_data = f'''
    <script>
        // Embedded data for standalone operation
        window.EMBEDDED_GRAPH_DATA = {json.dumps(graph_data, ensure_ascii=False)};
        window.EMBEDDED_GAP_DATA = {json.dumps(gap_data, ensure_ascii=False)};
    </script>
'''

    # Replace fetch logic with embedded data access
    # Find the useEffect with fetch calls and replace it
    old_fetch_code = '''            useEffect(() => {
                // Load graph data
                fetch('../knowledge_graph.json')
                    .then(res => res.json())
                    .then(data => setGraphData(data))
                    .catch(err => console.error('Failed to load graph:', err));

                // Load gap data
                fetch('../gap_candidates.json')
                    .then(res => res.json())
                    .then(data => setGapData(data))
                    .catch(err => console.error('Failed to load gaps:', err));
            }, []);'''

    new_fetch_code = '''            useEffect(() => {
                // Use embedded data (standalone mode) or fetch (server mode)
                if (window.EMBEDDED_GRAPH_DATA) {
                    setGraphData(window.EMBEDDED_GRAPH_DATA);
                } else {
                    fetch('../knowledge_graph.json')
                        .then(res => res.json())
                        .then(data => setGraphData(data))
                        .catch(err => console.error('Failed to load graph:', err));
                }

                if (window.EMBEDDED_GAP_DATA) {
                    setGapData(window.EMBEDDED_GAP_DATA);
                } else {
                    fetch('../gap_candidates.json')
                        .then(res => res.json())
                        .then(data => setGapData(data))
                        .catch(err => console.error('Failed to load gaps:', err));
                }
            }, []);'''

    # Apply replacements
    standalone_html = html_content.replace(old_fetch_code, new_fetch_code)

    # Insert embedded data before the closing </head> tag
    standalone_html = standalone_html.replace('</head>', embedded_data + '</head>')

    # Update title to indicate standalone version
    standalone_html = standalone_html.replace(
        '<title>SCS Knowledge Graph Visualization</title>',
        '<title>SCS Knowledge Graph Visualization (Standalone)</title>'
    )

    # Write standalone file
    print(f"Writing: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(standalone_html)

    # Calculate file size
    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"\nStandalone file created: {OUTPUT_FILE}")
    print(f"File size: {size_kb:.1f} KB")
    print(f"Nodes: {graph_data['metadata']['node_count']}")
    print(f"Edges: {graph_data['metadata']['edge_count']}")
    print(f"Gaps: {gap_data['metadata']['total_gaps']}")
    print("\nYou can now open index_standalone.html directly in your browser!")


if __name__ == "__main__":
    main()
