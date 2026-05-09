"use client";

import ReactFlow, { Background, Controls, Edge, Node } from "reactflow";
import "reactflow/dist/style.css";
import type { GraphResponse } from "@/lib/types";

export function ConflictGraph({ graph }: { graph: GraphResponse | null }) {
  if (!graph) {
    return <div className="panel">Run analysis to build the conflict graph.</div>;
  }

  const nodes: Node[] = graph.nodes.map((node, index) => ({
    id: node.id,
    position: {
      x: (index % 4) * 230,
      y: Math.floor(index / 4) * 110
    },
    data: { label: `${node.type}: ${node.label}` },
    style: {
      border: node.type === "participant" ? "2px solid #2563eb" : node.type === "claim" ? "1px solid #b45309" : "1px solid #15803d",
      borderRadius: 6,
      padding: 8,
      width: 190,
      fontSize: 12
    }
  }));

  const edges: Edge[] = graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label || edge.type,
    animated: edge.type === "conflicts_with",
    style: { stroke: edge.type === "conflicts_with" ? "#dc2626" : "#64748b" }
  }));

  return (
    <div className="panel" style={{ height: 520 }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
