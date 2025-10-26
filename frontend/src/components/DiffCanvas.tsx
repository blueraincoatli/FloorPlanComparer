import type { DiffEntity } from "../types/jobs";

type DiffCanvasProps = {
  entities: DiffEntity[];
};

export function DiffCanvas({ entities }: DiffCanvasProps) {
  const allPoints = entities.flatMap((entity) => entity.polygon.points);
  const xs = allPoints.map(([x]) => x);
  const ys = allPoints.map(([, y]) => y);
  const minX = Math.min(...xs, 0);
  const maxX = Math.max(...xs, 100);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 100);
  const padding = 10;
  const width = maxX - minX || 100;
  const height = maxY - minY || 100;
  const viewBox = `${minX - padding} ${minY - padding} ${width + padding * 2} ${height + padding * 2}`;

  return (
    <div className="diff-canvas">
      <svg viewBox={viewBox} role="img" aria-label="Diff preview">
        <defs>
          <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(226, 232, 240, 0.15)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect
          x={minX - padding}
          y={minY - padding}
          width={width + padding * 2}
          height={height + padding * 2}
          fill="url(#grid)"
        />
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
      <ul className="diff-legend">
        {entities.map((entity) => (
          <li key={entity.entity_id}>
            <span className={`dot dot-${entity.change_type}`} />
            <strong>{entity.label ?? entity.entity_id}</strong>
            <small>{entity.entity_type}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
