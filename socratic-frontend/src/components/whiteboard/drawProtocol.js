// Whiteboard draw protocol v1 — frontend half.
//
// Pure functions only (no React / Excalidraw imports) so everything here is
// unit-testable in plain Jest. Single source of truth for the wire format:
// docs/specs/whiteboard-draw-protocol-v1.md. The backend twin is
// Backend/app/services/providers/draw_protocol.py.

export const GRID = { width: 60, height: 40 };

export const DEFAULT_REGION = { x: 100, y: 100, width: 600, height: 400 };
const REGION_MARGIN = 40;
const MIN_REGION = { width: 600, height: 400 };
const REGION_ASPECT = 3 / 2; // width : height — keeps grid cells square

export const COLOR_HEX = { blue: '#2563eb', green: '#16a34a', red: '#dc2626' };
export const TEXT_SIZE_PX = { small: 16, medium: 24, large: 32 };
export const STROKE_WIDTH = { small: 1, medium: 2, large: 4 };
export const POINT_RADIUS_CELLS = { small: 0.2, medium: 0.3, large: 0.45 };
export const MATH_SCALE = { small: 0.8, medium: 1.2, large: 1.6 };
const ARC_MAX_STEP_DEG = 3;

// ── coordinate mapping ────────────────────────────────────────────────────────

export const gridToBoard = ([gx, gy], region) => [
  region.x + (gx * region.width) / GRID.width,
  region.y + (gy * region.height) / GRID.height,
];

export const boardToGrid = ([x, y], region) => [
  ((x - region.x) * GRID.width) / region.width,
  ((y - region.y) * GRID.height) / region.height,
];

// ── capture region ────────────────────────────────────────────────────────────

// The one coordinate frame shared by the screenshot, the board listing, and the
// AI's drawing actions (spec §1): content bbox + margin, padded to 3:2, min 600x400.
export function computeBoardRegion(elements) {
  const live = (elements || []).filter((el) => !el.isDeleted);
  if (!live.length) return { ...DEFAULT_REGION };

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const el of live) {
    minX = Math.min(minX, el.x);
    minY = Math.min(minY, el.y);
    maxX = Math.max(maxX, el.x + (el.width || 0));
    maxY = Math.max(maxY, el.y + (el.height || 0));
  }

  let width = Math.max(maxX - minX + 2 * REGION_MARGIN, MIN_REGION.width);
  let height = Math.max(maxY - minY + 2 * REGION_MARGIN, MIN_REGION.height);
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;

  // Pad the smaller dimension out to exactly 3:2 so grid cells stay square.
  if (width / height > REGION_ASPECT) {
    height = width / REGION_ASPECT;
  } else {
    width = height * REGION_ASPECT;
  }

  return { x: cx - width / 2, y: cy - height / 2, width, height };
}

// ── stroke smoothing ──────────────────────────────────────────────────────────

// Chaikin corner cutting, endpoint-preserving. Turns the model's coarse grid
// polyline into a hand-plausible curve before freedraw rendering.
export function chaikinSmooth(points, iterations = 2) {
  let pts = points;
  for (let iter = 0; iter < iterations; iter++) {
    if (pts.length < 3) return pts;
    const next = [pts[0]];
    for (let i = 0; i < pts.length - 1; i++) {
      const [x1, y1] = pts[i];
      const [x2, y2] = pts[i + 1];
      next.push([0.75 * x1 + 0.25 * x2, 0.75 * y1 + 0.25 * y2]);
      next.push([0.25 * x1 + 0.75 * x2, 0.25 * y1 + 0.75 * y2]);
    }
    next.push(pts[pts.length - 1]);
    pts = next;
  }
  return pts;
}

// ── action -> Excalidraw element skeleton ─────────────────────────────────────

const localizePoints = (boardPoints) => {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of boardPoints) {
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
  }
  return {
    x: minX,
    y: minY,
    // Floor at 1px: perfectly horizontal/vertical strokes otherwise produce a
    // zero-extent bbox, which NaNs Excalidraw's fit-to-content zoom math.
    width: Math.max(maxX - minX, 1),
    height: Math.max(maxY - minY, 1),
    points: boardPoints.map(([x, y]) => [x - minX, y - minY]),
  };
};

const strokeStyle = (action) => ({
  strokeColor: COLOR_HEX[action.color] || COLOR_HEX.blue,
  strokeWidth: STROKE_WIDTH[action.size] || STROKE_WIDTH.medium,
  strokeStyle: ['solid', 'dashed', 'dotted'].includes(action.style) ? action.style : 'solid',
});

// Sample an arc (grid-space center/radius/angles) into board-space points.
// 0° points along +x; angles run CLOCKWISE on screen because y grows downward,
// which is plain cos/sin in a y-down frame.
export function sampleArcPoints(action, region) {
  const [start, end] = action.angles;
  const sweep = end - start;
  const steps = Math.max(2, Math.ceil(Math.abs(sweep) / ARC_MAX_STEP_DEG));
  const cellW = region.width / GRID.width;
  const cellH = region.height / GRID.height;
  const [cx, cy] = gridToBoard(action.points[0], region);
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const rad = ((start + (sweep * i) / steps) * Math.PI) / 180;
    points.push([cx + action.radius * cellW * Math.cos(rad), cy + action.radius * cellH * Math.sin(rad)]);
  }
  return points;
}

// Map one wire action to a convertToExcalidrawElements skeleton, or null when the
// action is malformed or board-handled (erase and async math live in TutorBoard).
export function actionToSkeleton(action, region) {
  if (!action || typeof action !== 'object' || !region) return null;
  if (!Array.isArray(action.points)) return null;
  const badPoint = action.points.some(
    (p) => !Array.isArray(p) || p.length !== 2 || !Number.isFinite(p[0]) || !Number.isFinite(p[1])
  );
  if (badPoint) return null;

  const boardPoints = action.points.map((p) => gridToBoard(p, region));

  switch (action.op) {
    case 'stroke': {
      if (boardPoints.length < 2) return null;
      const smoothed = chaikinSmooth(boardPoints, 2);
      const { x, y, width, height, points } = localizePoints(smoothed);
      // Unlike the other skeleton types, convertToExcalidrawElements passes
      // "freedraw" through UNNORMALIZED (it's typed as a full element, not a
      // skeleton) — every base field must be present or Excalidraw's bounds
      // math NaNs (e.g. Math.cos(undefined) on a missing angle).
      return {
        type: 'freedraw',
        x,
        y,
        width,
        height,
        points,
        pressures: [],
        simulatePressure: true,
        lastCommittedPoint: points[points.length - 1],
        angle: 0,
        opacity: 100,
        roughness: 1,
        roundness: null,
        strokeStyle: 'solid',
        fillStyle: 'solid',
        backgroundColor: 'transparent',
        groupIds: [],
        frameId: null,
        boundElements: null,
        link: null,
        locked: false,
        isDeleted: false,
        seed: Math.floor(Math.random() * 2 ** 31),
        version: 1,
        ...strokeStyle(action),
      };
    }
    case 'line':
    case 'arrow': {
      if (boardPoints.length < 2) return null;
      const { x, y, width, height, points } = localizePoints(boardPoints);
      return {
        type: action.op,
        x,
        y,
        width,
        height,
        points,
        lastCommittedPoint: points[points.length - 1],
        ...(action.op === 'arrow' ? { endArrowhead: 'arrow', startArrowhead: null } : {}),
        ...strokeStyle(action),
      };
    }
    case 'text': {
      if (boardPoints.length !== 1) return null;
      if (typeof action.content !== 'string' || !action.content.trim()) return null;
      const [x, y] = boardPoints[0];
      return {
        type: 'text',
        x,
        y,
        text: action.content,
        fontSize: TEXT_SIZE_PX[action.size] || TEXT_SIZE_PX.medium,
        strokeColor: COLOR_HEX[action.color] || COLOR_HEX.blue,
      };
    }
    case 'point': {
      if (boardPoints.length !== 1) return null;
      const [cx, cy] = boardPoints[0];
      const cells = POINT_RADIUS_CELLS[action.size] || POINT_RADIUS_CELLS.medium;
      const r = cells * (region.width / GRID.width);
      const color = COLOR_HEX[action.color] || COLOR_HEX.blue;
      return {
        type: 'ellipse',
        x: cx - r,
        y: cy - r,
        width: 2 * r,
        height: 2 * r,
        backgroundColor: color,
        fillStyle: 'solid',
        strokeColor: color,
        strokeWidth: 1,
      };
    }
    case 'arc': {
      if (boardPoints.length !== 1) return null;
      if (!Number.isFinite(action.radius) || action.radius <= 0) return null;
      if (!Array.isArray(action.angles) || action.angles.length !== 2) return null;
      if (!action.angles.every(Number.isFinite)) return null;
      const sampled = sampleArcPoints(action, region);
      const { x, y, width, height, points } = localizePoints(sampled);
      return {
        type: 'line',
        x,
        y,
        width,
        height,
        points,
        lastCommittedPoint: points[points.length - 1],
        ...strokeStyle(action),
      };
    }
    case 'ellipse':
    case 'rect': {
      if (boardPoints.length !== 2) return null;
      const [[x1, y1], [x2, y2]] = boardPoints;
      if (x2 <= x1 || y2 <= y1) return null;
      return {
        type: action.op === 'rect' ? 'rectangle' : 'ellipse',
        x: x1,
        y: y1,
        width: x2 - x1,
        height: y2 - y1,
        backgroundColor: 'transparent',
        ...strokeStyle(action),
      };
    }
    default:
      // erase and math are handled by TutorBoard (scene mutation / async render).
      return null;
  }
}

// ── scene -> symbolic board listing ───────────────────────────────────────────

const round1 = (n) => Math.round(n * 10) / 10;

// Serialize the scene for the model (spec §2). Returns the wire listing plus the
// per-turn alias -> real Excalidraw id map (erase targets resolve through it).
export function elementsToBoardListing(elements, region) {
  const listing = [];
  const aliasMap = {};
  let studentCount = 0;
  let tutorCount = 0;

  for (const el of (elements || []).filter((e) => !e.isDeleted)) {
    const isTutor = el.customData && el.customData.source === 'ai';
    const alias = isTutor ? `t${++tutorCount}` : `s${++studentCount}`;
    aliasMap[alias] = el.id;

    const [gx1, gy1] = boardToGrid([el.x, el.y], region);
    const [gx2, gy2] = boardToGrid([el.x + (el.width || 0), el.y + (el.height || 0)], region);

    // Text elements carry their text; math images carry the LaTeX they render.
    const content =
      typeof el.text === 'string' ? el.text : el.customData?.latex ?? null;

    listing.push({
      id: alias,
      source: isTutor ? 'tutor' : 'student',
      type: el.type,
      gridBox: [round1(gx1), round1(gy1), round1(gx2), round1(gy2)],
      content: typeof content === 'string' ? content.slice(0, 120) : null,
    });
  }
  return { listing, aliasMap };
}

// ── grid overlay for the captured screenshot ──────────────────────────────────

// Stamp faint gridlines every 5 cells + edge coordinate labels onto a capture
// canvas that covers exactly boardRegion (spec §1). Mutates the canvas.
export function stampGrid(canvas) {
  const ctx = canvas.getContext('2d');
  const cellW = canvas.width / GRID.width;
  const cellH = canvas.height / GRID.height;

  ctx.save();
  ctx.strokeStyle = 'rgba(148, 163, 184, 0.35)';
  ctx.fillStyle = 'rgba(100, 116, 139, 0.8)';
  ctx.lineWidth = 1;
  ctx.font = `${Math.max(10, Math.round(cellH * 0.55))}px Arial`;

  for (let gx = 5; gx < GRID.width; gx += 5) {
    const x = gx * cellW;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
    ctx.fillText(String(gx), x + 2, 12);
    ctx.fillText(String(gx), x + 2, canvas.height - 4);
  }
  for (let gy = 5; gy < GRID.height; gy += 5) {
    const y = gy * cellH;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
    ctx.fillText(String(gy), 2, y - 2);
    ctx.fillText(String(gy), canvas.width - 20, y - 2);
  }
  ctx.restore();
}
