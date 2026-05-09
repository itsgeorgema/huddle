"use client";

import ReactFlow, { Background, Controls, Edge, MarkerType, Node } from "reactflow";
import "reactflow/dist/style.css";
import type { GraphResponse } from "@/lib/types";

export function ConflictGraph({ graph }: { graph: GraphResponse | null }) {
  if (!graph) {
    return (
      <div className="panel graph-frame empty-state">
        Run analysis to build the conflict graph.
      </div>
    );
  }

  const nodes: Node[] = graph.nodes.map((node, index) => {
    const style = nodeStyle(node.type);

    return {
      id: node.id,
      position: {
        x: (index % 4) * 255 + (Math.floor(index / 4) % 2) * 55,
        y: Math.floor(index / 4) * 132
      },
      data: { label: `${labelForType(node.type)}: ${node.label}` },
      style
    };
  });

  const edges: Edge[] = graph.edges.map((edge) => {
    const conflict = edge.type === "conflicts_with";

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label || edge.type.replaceAll("_", " "),
      animated: conflict,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: conflict ? "#8e2f2a" : "#69727d"
      },
      style: {
        stroke: conflict ? "#8e2f2a" : "#69727d",
        strokeWidth: conflict ? 2.25 : 1.35
      },
      labelStyle: {
        fill: "#3f4852",
        fontWeight: 700
      },
      labelBgStyle: {
        fill: "#fffdf8",
        fillOpacity: 0.86
      }
    };
  });

  return (
    <div className="panel graph-frame">
      <div className="graph-legend">
        <Legend swatch="" label="Participant" />
        <Legend swatch="claim" label="Claim" />
        <Legend swatch="topic" label="Topic" />
        <Legend swatch="conflict" label="Conflict edge" />
      </div>
      <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.35} maxZoom={1.35}>
        <Background color="#d4c7b4" gap={28} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="legend-item">
      <span className={`legend-swatch ${swatch}`} />
      {label}
    </span>
  );
}

function labelForType(type: string) {
  if (type === "participant") return "Participant";
  if (type === "claim") return "Claim";
  return "Topic";
}

function nodeStyle(type: string) {
  const shared = {
    borderRadius: 8,
    padding: 10,
    width: 212,
    minHeight: 54,
    fontSize: 12,
    lineHeight: 1.35,
    color: "#171b1f",
    boxShadow: "0 14px 34px -28px rgba(49, 38, 25, 0.65)"
  };

  if (type === "participant") {
    return {
      ...shared,
      border: "2px solid #254a5d",
      background: "#f8f3e8"
    };
  }

  if (type === "claim") {
    return {
      ...shared,
      border: "1px solid #b98433",
      background: "#fffaf1"
    };
  }

  return {
    ...shared,
    border: "1px solid #5d6542",
    background: "#f1efe4"
  };
}
