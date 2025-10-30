import type { CSSProperties } from "react";

import type { DiffEntity } from "../types/jobs";

type DiffCanvasProps = {
  entities: DiffEntity[];
  height?: number | string;
  showLegend?: boolean;
  className?: string;
  showBackground?: boolean;
  backgroundEntities?: DiffEntity[];
};

export function DiffCanvas({
  entities,
  height = 360,
  showLegend = false,  // 默认隐藏图例，简化UI
  className,
  showBackground = false,
  backgroundEntities,
}: DiffCanvasProps) {
  const combined = showBackground && backgroundEntities ? [...backgroundEntities, ...entities] : entities;
  const allPoints = combined.flatMap((entity) => entity.polygon.points);
  const xs = allPoints.map(([x]) => x);
  const ys = allPoints.map(([, y]) => y);
  const minX = Math.min(...xs, 0);
  const maxX = Math.max(...xs, 100);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 100);
  const padding = 10;
  const width = maxX - minX || 100;
  const heightValue = maxY - minY || 100;
  const viewBox = `${minX - padding} ${minY - padding} ${width + padding * 2} ${heightValue + padding * 2}`;
  const wrapperClass = ["diff-canvas", className].filter(Boolean).join(" ");
  const svgStyle: CSSProperties = {
    width: "100%",
    height: typeof height === "number" ? `${height}px` : height,
  };

  return (
    <div className={wrapperClass}>
      <svg viewBox={viewBox} role="img" aria-label="Diff preview" style={svgStyle}>
        <defs>
          <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(226, 232, 240, 0.15)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect
          x={minX - padding}
          y={minY - padding}
          width={width + padding * 2}
          height={heightValue + padding * 2}
          fill="url(#grid)"
        />
        {showBackground && backgroundEntities?.map((entity) => (
          <polygon
            key={`bg-${entity.entity_id}`}
            points={entity.polygon.points.map((point) => point.join(",")).join(" ")}
            className="diff-shape diff-background"
            fill="rgba(148, 163, 184, 0.12)"
            stroke="rgba(148, 163, 184, 0.3)"
            strokeWidth={1}
          >
            <title>{entity.label ?? entity.entity_id}</title>
          </polygon>
        ))}
        {entities.map((entity) => (
          <polygon
            key={entity.entity_id}
            points={entity.polygon.points.map((point) => point.join(",")).join(" ")}
            className={`diff-shape diff-${entity.change_type}`}
          >
            <title>{entity.label ?? entity.entity_id}</title>
          </polygon>
        ))}
      </svg>
      {showLegend && (
        <ul className="diff-legend">
          {entities.map((entity) => (
            <li key={entity.entity_id}>
              <span className={`dot dot-${entity.change_type}`} />
              <strong>{entity.label ?? entity.entity_id}</strong>
              <small>{entity.entity_type}</small>
            </li>
          ))}
          {showBackground && backgroundEntities?.length ? (
            <li key="background">
              <span className="dot dot-background" />
              <strong>原图/改图覆盖层</strong>
              <small>背景实体</small>
            </li>
          ) : null}
        </ul>
      )}
    </div>
  );
}
