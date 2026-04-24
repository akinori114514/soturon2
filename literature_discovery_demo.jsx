import React, { useState, useEffect, useRef, useCallback } from 'react';

// Sample concept data simulating extraction from SCS-related papers
const SAMPLE_PAPERS = [
  {
    source: "horiuchi_2019_reverse_adaptation.pdf",
    domain: "逆適応論",
    concepts: [
      { concept: "逆適応", type: "theory", context: "日本的経営の要素が中国で変容して定着する現象" },
      { concept: "信用スコア", type: "phenomenon", context: "個人の行動履歴に基づく数値化された信頼指標" },
      { concept: "行動変容", type: "mechanism", context: "スコアリングによる自発的な行動修正" },
      { concept: "制度移転", type: "theory", context: "ある国の制度が別の国で採用される過程" },
      { concept: "日中比較", type: "method", context: "日本と中国の制度を比較分析する手法" },
    ]
  },
  {
    source: "ssali_2023_digital_authoritarianism.pdf",
    domain: "デジタル権威主義",
    concepts: [
      { concept: "デジタル権威主義", type: "theory", context: "テクノロジーを活用した権威主義的統治形態" },
      { concept: "社会信用システム", type: "phenomenon", context: "中国の社会信用体系による市民管理" },
      { concept: "行動変容", type: "mechanism", context: "監視による自己規律と自発的服従" },
      { concept: "誘惑的権威主義", type: "theory", context: "罰則よりもインセンティブによる統治" },
      { concept: "アルゴリズム統治", type: "phenomenon", context: "アルゴリズムによる社会管理と意思決定" },
    ]
  },
  {
    source: "zuboff_2019_surveillance_capitalism.pdf",
    domain: "監視資本主義",
    concepts: [
      { concept: "監視資本主義", type: "theory", context: "行動データの収集と予測による新しい資本蓄積形態" },
      { concept: "行動余剰", type: "phenomenon", context: "サービス改善に不要な余剰行動データ" },
      { concept: "予測市場", type: "mechanism", context: "行動予測を売買する新しい市場形態" },
      { concept: "データ抽出", type: "mechanism", context: "ユーザーからの継続的な行動データ収集" },
      { concept: "行動変容", type: "mechanism", context: "プラットフォームによる行動誘導と修正" },
    ]
  },
  {
    source: "creemers_2018_scs_policy.pdf",
    domain: "中国政策研究",
    concepts: [
      { concept: "社会信用システム", type: "phenomenon", context: "2014年に発表された中国の社会管理計画" },
      { concept: "ブラックリスト", type: "mechanism", context: "信用失墜者の公開リストと制裁措置" },
      { concept: "連合懲戒", type: "mechanism", context: "複数機関による協調的制裁システム" },
      { concept: "信用修復", type: "phenomenon", context: "失った信用を回復するプロセス" },
      { concept: "信用スコア", type: "phenomenon", context: "芝麻信用などの民間信用評価" },
    ]
  },
  {
    source: "kostka_2019_scs_attitudes.pdf",
    domain: "世論研究",
    concepts: [
      { concept: "社会信用システム", type: "phenomenon", context: "中国市民の社会信用システムに対する態度調査" },
      { concept: "社会的信頼", type: "phenomenon", context: "他者や制度への信頼度" },
      { concept: "プライバシー懸念", type: "phenomenon", context: "個人情報収集に対する不安" },
      { concept: "受容性", type: "phenomenon", context: "システムに対する市民の許容度" },
      { concept: "政府信頼", type: "phenomenon", context: "政府への信頼がシステム受容に影響" },
    ]
  },
  {
    source: "liang_2018_privacy_china.pdf",
    domain: "プライバシー研究",
    concepts: [
      { concept: "プライバシー懸念", type: "phenomenon", context: "中国におけるプライバシー意識の変容" },
      { concept: "データ保護", type: "mechanism", context: "個人データの法的保護枠組み" },
      { concept: "監視技術", type: "phenomenon", context: "顔認識やIoTによる監視インフラ" },
      { concept: "同意なき収集", type: "phenomenon", context: "暗黙の同意による大規模データ収集" },
      { concept: "データ抽出", type: "mechanism", context: "行動データの継続的収集と蓄積" },
    ]
  }
];

// Build knowledge graph
function buildGraph(papers) {
  const nodes = new Map();
  const edges = [];
  
  papers.forEach(paper => {
    const conceptsInPaper = [];
    
    paper.concepts.forEach(c => {
      const key = c.concept.toLowerCase();
      if (!nodes.has(key)) {
        nodes.set(key, {
          id: key,
          label: c.concept,
          type: c.type,
          sources: new Set([paper.source]),
          domains: new Set([paper.domain]),
          contexts: [{ source: paper.source, text: c.context }]
        });
      } else {
        const node = nodes.get(key);
        node.sources.add(paper.source);
        node.domains.add(paper.domain);
        node.contexts.push({ source: paper.source, text: c.context });
      }
      conceptsInPaper.push(key);
    });
    
    // Create edges between concepts in same paper
    for (let i = 0; i < conceptsInPaper.length; i++) {
      for (let j = i + 1; j < conceptsInPaper.length; j++) {
        const edgeKey = [conceptsInPaper[i], conceptsInPaper[j]].sort().join('--');
        const existing = edges.find(e => e.id === edgeKey);
        if (existing) {
          existing.weight++;
          existing.sources.add(paper.source);
        } else {
          edges.push({
            id: edgeKey,
            source: conceptsInPaper[i],
            target: conceptsInPaper[j],
            weight: 1,
            sources: new Set([paper.source])
          });
        }
      }
    }
  });
  
  return {
    nodes: Array.from(nodes.values()).map(n => ({
      ...n,
      sources: Array.from(n.sources),
      domains: Array.from(n.domains)
    })),
    edges: edges.map(e => ({
      ...e,
      sources: Array.from(e.sources)
    }))
  };
}

// Find gaps (Swanson's ABC model)
function findGaps(graph) {
  const { nodes, edges } = graph;
  const edgeSet = new Set(edges.map(e => e.id));
  
  const neighbors = new Map();
  nodes.forEach(n => neighbors.set(n.id, new Set()));
  edges.forEach(e => {
    neighbors.get(e.source).add(e.target);
    neighbors.get(e.target).add(e.source);
  });
  
  const gaps = [];
  
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const n1 = nodes[i];
      const n2 = nodes[j];
      const edgeKey = [n1.id, n2.id].sort().join('--');
      
      // Skip if directly connected
      if (edgeSet.has(edgeKey)) continue;
      
      // Find common neighbors
      const neighbors1 = neighbors.get(n1.id);
      const neighbors2 = neighbors.get(n2.id);
      const common = [...neighbors1].filter(x => neighbors2.has(x));
      
      if (common.length === 0) continue;
      
      // Skip if from same sources only
      const sources1 = new Set(n1.sources);
      const sources2 = new Set(n2.sources);
      const overlap = [...sources1].filter(x => sources2.has(x));
      if (overlap.length === sources1.size && overlap.length === sources2.size) continue;
      
      const union = new Set([...neighbors1, ...neighbors2]);
      const jaccard = common.length / union.size;
      
      gaps.push({
        conceptA: n1,
        conceptB: n2,
        commonNeighbors: common.map(c => nodes.find(n => n.id === c)?.label || c),
        jaccard: jaccard,
        bridgePotential: common.length,
        novelty: sources1.size !== sources2.size ? 'high' : 'medium'
      });
    }
  }
  
  return gaps.sort((a, b) => b.bridgePotential - a.bridgePotential);
}

// Generate hypothesis (simulated)
const HYPOTHESES = {
  '逆適応--デジタル権威主義': {
    hypothesis: "中国のデジタル権威主義は、日本的経営の要素が「逆適応」した結果として解釈できる",
    mechanism: "逆適応（制度移転） → 行動変容メカニズムの導入 → デジタル技術との融合 → デジタル権威主義の形成",
    testability: "medium",
    testMethod: "日中の信用スコアシステムの比較制度分析、歴史的な制度移転の追跡調査",
    significance: "中国のSCSを外来制度の変容として捉える新しい分析視座を提供",
    confidence: 0.75
  },
  '監視資本主義--社会信用システム': {
    hypothesis: "社会信用システムは監視資本主義の国家版であり、両者は「行動余剰」の活用方法が異なる",
    mechanism: "データ抽出 → 行動余剰の生成 → 予測/統治への活用（民間=利益、国家=秩序）",
    testability: "high",
    testMethod: "AlipayとGAFAの行動データ活用比較、収益モデルvs統治モデルの構造分析",
    significance: "官民のデータ活用の共通構造と差異を明らかにし、グローバルな監視経済の理解に貢献",
    confidence: 0.85
  },
  '誘惑的権威主義--信用スコア': {
    hypothesis: "信用スコアは「誘惑的権威主義」の核心技術であり、罰則なき統治を可能にする",
    mechanism: "信用スコア → ポジティブインセンティブ → 自発的行動変容 → 強制なき服従",
    testability: "medium",
    testMethod: "芝麻信用ユーザーの行動追跡調査、インセンティブ設計の分析",
    significance: "権威主義の「ソフト化」メカニズムを解明し、民主主義社会への示唆を提供",
    confidence: 0.8
  },
  '逆適応--監視資本主義': {
    hypothesis: "監視資本主義の技術が中国で「逆適応」し、国家主導の社会管理システムに変容した",
    mechanism: "西洋発の監視技術 → 中国での採用 → 国家目的への転用 → SCSとしての制度化",
    testability: "medium",
    testMethod: "GAFAと中国テック企業の技術移転史、制度変容の事例研究",
    significance: "グローバルな監視技術の多様な発展経路を理解する理論的枠組み",
    confidence: 0.7
  }
};

function getHypothesis(conceptA, conceptB) {
  const key1 = `${conceptA}--${conceptB}`;
  const key2 = `${conceptB}--${conceptA}`;
  
  if (HYPOTHESES[key1]) return HYPOTHESES[key1];
  if (HYPOTHESES[key2]) return HYPOTHESES[key2];
  
  // Generate a generic hypothesis
  return {
    hypothesis: `${conceptA}と${conceptB}の間には、共通の橋渡し概念を通じた未発見の関係がある可能性がある`,
    mechanism: "共通概念を媒介とした間接的な因果関係または相関関係",
    testability: "low",
    testMethod: "両概念を扱う追加文献の収集と体系的レビュー",
    significance: "新しい学際的研究の可能性を示唆",
    confidence: 0.5
  };
}

// Color schemes
const TYPE_COLORS = {
  theory: '#8b5cf6',
  phenomenon: '#06b6d4',
  mechanism: '#f59e0b',
  method: '#10b981',
  entity: '#ec4899'
};

const DOMAIN_COLORS = {
  '逆適応論': '#8b5cf6',
  'デジタル権威主義': '#ef4444',
  '監視資本主義': '#f59e0b',
  '中国政策研究': '#06b6d4',
  '世論研究': '#10b981',
  'プライバシー研究': '#ec4899'
};

export default function LiteratureDiscoveryDemo() {
  const [graph, setGraph] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [selectedGap, setSelectedGap] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hypothesis, setHypothesis] = useState(null);
  const [view, setView] = useState('graph');
  const [colorBy, setColorBy] = useState('type');
  const [isGenerating, setIsGenerating] = useState(false);
  const svgRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [nodePositions, setNodePositions] = useState({});
  const [dragging, setDragging] = useState(null);

  useEffect(() => {
    const g = buildGraph(SAMPLE_PAPERS);
    setGraph(g);
    const foundGaps = findGaps(g);
    setGaps(foundGaps);
    
    // Initialize node positions in a circle
    const positions = {};
    const centerX = 400;
    const centerY = 250;
    const radius = 180;
    g.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / g.nodes.length;
      positions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });
    setNodePositions(positions);
  }, []);

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
    setSelectedGap(null);
    setHypothesis(null);
  }, []);

  const handleGapClick = useCallback((gap) => {
    setSelectedGap(gap);
    setSelectedNode(null);
    setHypothesis(null);
  }, []);

  const generateHypothesis = useCallback(() => {
    if (!selectedGap) return;
    setIsGenerating(true);
    
    setTimeout(() => {
      const h = getHypothesis(selectedGap.conceptA.label, selectedGap.conceptB.label);
      setHypothesis(h);
      setIsGenerating(false);
    }, 1500);
  }, [selectedGap]);

  const handleMouseDown = useCallback((e, nodeId) => {
    e.stopPropagation();
    setDragging(nodeId);
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (!dragging || !svgRef.current) return;
    
    const svg = svgRef.current;
    const rect = svg.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setNodePositions(prev => ({
      ...prev,
      [dragging]: { x, y }
    }));
  }, [dragging]);

  const handleMouseUp = useCallback(() => {
    setDragging(null);
  }, []);

  if (!graph) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900 text-white">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  const getNodeColor = (node) => {
    if (colorBy === 'type') return TYPE_COLORS[node.type] || '#6b7280';
    if (colorBy === 'domain') return DOMAIN_COLORS[node.domains[0]] || '#6b7280';
    return '#6b7280';
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-cyan-400 mb-2">
            Literature-Based Discovery
          </h1>
          <p className="text-slate-400 text-sm">
            Swanson (1986) の手法をLLMで実装 — 異なる論文の概念間の「未発見の繋がり」を発見し、研究仮説を生成
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-2xl font-bold text-violet-400">{SAMPLE_PAPERS.length}</div>
            <div className="text-slate-400 text-sm">論文数</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-2xl font-bold text-cyan-400">{graph.nodes.length}</div>
            <div className="text-slate-400 text-sm">概念ノード</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-2xl font-bold text-amber-400">{graph.edges.length}</div>
            <div className="text-slate-400 text-sm">共起エッジ</div>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
            <div className="text-2xl font-bold text-emerald-400">{gaps.length}</div>
            <div className="text-slate-400 text-sm">発見されたギャップ</div>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setView('graph')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              view === 'graph'
                ? 'bg-violet-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            知識グラフ
          </button>
          <button
            onClick={() => setView('gaps')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              view === 'gaps'
                ? 'bg-violet-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            ギャップ一覧
          </button>
          <button
            onClick={() => setView('papers')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              view === 'papers'
                ? 'bg-violet-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            論文データ
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Main View */}
          <div className="col-span-2">
            {view === 'graph' && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="font-semibold">概念知識グラフ</h2>
                  <div className="flex gap-2">
                    <select
                      value={colorBy}
                      onChange={(e) => setColorBy(e.target.value)}
                      className="bg-slate-700 text-sm rounded px-2 py-1 border border-slate-600"
                    >
                      <option value="type">概念タイプで色分け</option>
                      <option value="domain">研究領域で色分け</option>
                    </select>
                  </div>
                </div>
                
                <svg
                  ref={svgRef}
                  width={dimensions.width}
                  height={dimensions.height}
                  className="bg-slate-900 rounded"
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                >
                  {/* Edges */}
                  {graph.edges.map(edge => {
                    const sourcePos = nodePositions[edge.source];
                    const targetPos = nodePositions[edge.target];
                    if (!sourcePos || !targetPos) return null;
                    
                    const isHighlighted = selectedNode && 
                      (edge.source === selectedNode.id || edge.target === selectedNode.id);
                    
                    return (
                      <line
                        key={edge.id}
                        x1={sourcePos.x}
                        y1={sourcePos.y}
                        x2={targetPos.x}
                        y2={targetPos.y}
                        stroke={isHighlighted ? '#8b5cf6' : '#334155'}
                        strokeWidth={isHighlighted ? 2 : Math.min(edge.weight, 3)}
                        opacity={selectedNode ? (isHighlighted ? 1 : 0.2) : 0.6}
                      />
                    );
                  })}
                  
                  {/* Gap highlight */}
                  {selectedGap && (
                    <line
                      x1={nodePositions[selectedGap.conceptA.id]?.x}
                      y1={nodePositions[selectedGap.conceptA.id]?.y}
                      x2={nodePositions[selectedGap.conceptB.id]?.x}
                      y2={nodePositions[selectedGap.conceptB.id]?.y}
                      stroke="#f59e0b"
                      strokeWidth={3}
                      strokeDasharray="8,4"
                      opacity={0.8}
                    />
                  )}
                  
                  {/* Nodes */}
                  {graph.nodes.map(node => {
                    const pos = nodePositions[node.id];
                    if (!pos) return null;
                    
                    const isSelected = selectedNode?.id === node.id;
                    const isGapNode = selectedGap && 
                      (selectedGap.conceptA.id === node.id || selectedGap.conceptB.id === node.id);
                    const isBridge = selectedGap && 
                      selectedGap.commonNeighbors.map(n => n.toLowerCase()).includes(node.id);
                    
                    return (
                      <g key={node.id}>
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r={isSelected || isGapNode ? 12 : 8}
                          fill={getNodeColor(node)}
                          stroke={isGapNode ? '#f59e0b' : isBridge ? '#10b981' : '#1e293b'}
                          strokeWidth={isGapNode || isBridge ? 3 : 2}
                          className="cursor-pointer transition-all"
                          onClick={() => handleNodeClick(node)}
                          onMouseDown={(e) => handleMouseDown(e, node.id)}
                          opacity={selectedNode && !isSelected ? 0.4 : 1}
                        />
                        <text
                          x={pos.x}
                          y={pos.y + 22}
                          textAnchor="middle"
                          fill="#94a3b8"
                          fontSize={10}
                          className="pointer-events-none select-none"
                          opacity={selectedNode && !isSelected ? 0.3 : 1}
                        >
                          {node.label}
                        </text>
                      </g>
                    );
                  })}
                </svg>
                
                {/* Legend */}
                <div className="mt-4 flex flex-wrap gap-4 text-xs">
                  {colorBy === 'type' ? (
                    Object.entries(TYPE_COLORS).map(([type, color]) => (
                      <div key={type} className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-slate-400">{type}</span>
                      </div>
                    ))
                  ) : (
                    Object.entries(DOMAIN_COLORS).map(([domain, color]) => (
                      <div key={domain} className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-slate-400">{domain}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {view === 'gaps' && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 max-h-[600px] overflow-y-auto">
                <h2 className="font-semibold mb-4">発見されたギャップ（上位10件）</h2>
                <div className="space-y-3">
                  {gaps.slice(0, 10).map((gap, i) => (
                    <div
                      key={i}
                      onClick={() => {
                        handleGapClick(gap);
                        setView('graph');
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition ${
                        selectedGap === gap
                          ? 'bg-violet-900/30 border-violet-500'
                          : 'bg-slate-900 border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-violet-400 font-medium">{gap.conceptA.label}</span>
                          <span className="text-amber-400">⟷</span>
                          <span className="text-cyan-400 font-medium">{gap.conceptB.label}</span>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          gap.novelty === 'high' 
                            ? 'bg-emerald-900/50 text-emerald-400' 
                            : 'bg-slate-700 text-slate-400'
                        }`}>
                          {gap.novelty === 'high' ? '高新規性' : '中新規性'}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        <span className="text-slate-500">橋渡し概念:</span>{' '}
                        {gap.commonNeighbors.join(', ')}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        Bridge Potential: {gap.bridgePotential} | Jaccard: {gap.jaccard.toFixed(3)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {view === 'papers' && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 max-h-[600px] overflow-y-auto">
                <h2 className="font-semibold mb-4">サンプル論文データ</h2>
                <div className="space-y-4">
                  {SAMPLE_PAPERS.map((paper, i) => (
                    <div key={i} className="bg-slate-900 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <span 
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: DOMAIN_COLORS[paper.domain] }}
                        />
                        <span className="font-medium text-sm">{paper.source}</span>
                        <span className="text-xs text-slate-500">({paper.domain})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {paper.concepts.map((c, j) => (
                          <span
                            key={j}
                            className="text-xs px-2 py-1 rounded"
                            style={{ 
                              backgroundColor: `${TYPE_COLORS[c.type]}20`,
                              color: TYPE_COLORS[c.type]
                            }}
                          >
                            {c.concept}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Detail Panel */}
          <div className="space-y-4">
            {selectedNode && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getNodeColor(selectedNode) }}
                  />
                  {selectedNode.label}
                </h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-slate-500">タイプ:</span>
                    <span className="ml-2">{selectedNode.type}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">出現論文:</span>
                    <div className="mt-1 space-y-1">
                      {selectedNode.sources.map((s, i) => (
                        <div key={i} className="text-xs text-slate-400">• {s}</div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">文脈:</span>
                    <div className="mt-1 space-y-2">
                      {selectedNode.contexts.slice(0, 2).map((ctx, i) => (
                        <div key={i} className="text-xs bg-slate-900 p-2 rounded">
                          <div className="text-slate-500 mb-1">{ctx.source}</div>
                          <div className="text-slate-300">{ctx.text}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedGap && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <h3 className="font-semibold mb-3 text-amber-400">ギャップ詳細</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-violet-400">{selectedGap.conceptA.label}</span>
                    <span className="text-amber-400">⟷</span>
                    <span className="text-cyan-400">{selectedGap.conceptB.label}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">橋渡し概念:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedGap.commonNeighbors.map((n, i) => (
                        <span key={i} className="text-xs bg-emerald-900/30 text-emerald-400 px-2 py-0.5 rounded">
                          {n}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-900 p-2 rounded">
                      <div className="text-slate-500">Bridge Potential</div>
                      <div className="text-lg font-bold">{selectedGap.bridgePotential}</div>
                    </div>
                    <div className="bg-slate-900 p-2 rounded">
                      <div className="text-slate-500">Jaccard類似度</div>
                      <div className="text-lg font-bold">{selectedGap.jaccard.toFixed(3)}</div>
                    </div>
                  </div>
                  
                  <button
                    onClick={generateHypothesis}
                    disabled={isGenerating}
                    className="w-full py-2 bg-gradient-to-r from-violet-600 to-cyan-600 rounded-lg font-medium hover:from-violet-500 hover:to-cyan-500 transition disabled:opacity-50"
                  >
                    {isGenerating ? '仮説生成中...' : '🔬 仮説を生成'}
                  </button>
                </div>
              </div>
            )}

            {hypothesis && (
              <div className="bg-slate-800 rounded-lg border border-violet-500/50 p-4">
                <h3 className="font-semibold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-cyan-400">
                  生成された仮説
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="bg-slate-900 p-3 rounded border-l-4 border-violet-500">
                    <p className="text-slate-200">{hypothesis.hypothesis}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">メカニズム:</span>
                    <p className="text-slate-300 text-xs mt-1">{hypothesis.mechanism}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-slate-500 text-xs">検証可能性</span>
                      <div className={`text-sm font-medium ${
                        hypothesis.testability === 'high' ? 'text-emerald-400' :
                        hypothesis.testability === 'medium' ? 'text-amber-400' : 'text-slate-400'
                      }`}>
                        {hypothesis.testability}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500 text-xs">確信度</span>
                      <div className="text-sm font-medium text-violet-400">
                        {(hypothesis.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500 text-xs">検証方法:</span>
                    <p className="text-slate-400 text-xs mt-1">{hypothesis.testMethod}</p>
                  </div>
                  <div>
                    <span className="text-slate-500 text-xs">研究意義:</span>
                    <p className="text-slate-400 text-xs mt-1">{hypothesis.significance}</p>
                  </div>
                </div>
              </div>
            )}

            {!selectedNode && !selectedGap && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <h3 className="font-semibold mb-3">使い方</h3>
                <ul className="space-y-2 text-sm text-slate-400">
                  <li className="flex items-start gap-2">
                    <span className="text-violet-400">1.</span>
                    グラフのノードをクリックして概念の詳細を確認
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400">2.</span>
                    「ギャップ一覧」で未発見の繋がりを探索
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400">3.</span>
                    ギャップを選択して「仮説を生成」をクリック
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400">4.</span>
                    ノードはドラッグで移動可能
                  </li>
                </ul>
                <div className="mt-4 p-3 bg-slate-900 rounded text-xs text-slate-500">
                  <strong className="text-slate-400">Swansonの発見（1986）:</strong> 魚油とレイノー病の関係を、「血液粘度」という橋渡し概念を通じて発見した。
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-slate-600">
          デモ用サンプルデータ — 実際の研究には論文PDFを{' '}
          <code className="bg-slate-800 px-1 rounded">extract_concepts.py</code> で処理してください
        </div>
      </div>
    </div>
  );
}
