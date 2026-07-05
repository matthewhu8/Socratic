import {
  DEFAULT_REGION,
  GRID,
  actionToSkeleton,
  boardToGrid,
  chaikinSmooth,
  computeBoardRegion,
  elementsToBoardListing,
  gridToBoard,
  sampleArcPoints,
} from '../drawProtocol';

const region = { x: 100, y: 100, width: 600, height: 400 };

const makeAction = (overrides = {}) => ({
  op: 'stroke',
  points: [[10, 10], [20, 15], [30, 12]],
  content: null,
  color: 'blue',
  size: null,
  style: null,
  radius: null,
  angles: null,
  target: null,
  ...overrides,
});

// ── coordinate mapping ────────────────────────────────────────────────────────

describe('grid mapping', () => {
  it('maps grid corners to region corners', () => {
    expect(gridToBoard([0, 0], region)).toEqual([100, 100]);
    expect(gridToBoard([60, 40], region)).toEqual([700, 500]);
    expect(gridToBoard([30, 20], region)).toEqual([400, 300]);
  });

  it('round-trips board -> grid -> board', () => {
    const [gx, gy] = boardToGrid([250, 333], region);
    const [x, y] = gridToBoard([gx, gy], region);
    expect(x).toBeCloseTo(250);
    expect(y).toBeCloseTo(333);
  });
});

// ── capture region ────────────────────────────────────────────────────────────

describe('computeBoardRegion', () => {
  it('returns the default region for an empty board', () => {
    expect(computeBoardRegion([])).toEqual(DEFAULT_REGION);
    expect(computeBoardRegion(null)).toEqual(DEFAULT_REGION);
  });

  it('ignores deleted elements', () => {
    const els = [{ x: 5000, y: 5000, width: 10, height: 10, isDeleted: true }];
    expect(computeBoardRegion(els)).toEqual(DEFAULT_REGION);
  });

  it('is always 3:2 and covers content plus margin', () => {
    const els = [
      { x: 200, y: 300, width: 100, height: 50 },
      { x: 900, y: 350, width: 40, height: 400 },
    ];
    const r = computeBoardRegion(els);
    expect(r.width / r.height).toBeCloseTo(1.5);
    expect(r.x).toBeLessThanOrEqual(200 - 0); // content inside
    expect(r.x + r.width).toBeGreaterThanOrEqual(940);
    expect(r.y + r.height).toBeGreaterThanOrEqual(750);
  });

  it('enforces the minimum region size', () => {
    const els = [{ x: 400, y: 400, width: 10, height: 10 }];
    const r = computeBoardRegion(els);
    expect(r.width).toBeGreaterThanOrEqual(600);
    expect(r.height).toBeGreaterThanOrEqual(400);
  });
});

// ── smoothing ────────────────────────────────────────────────────────────────

describe('chaikinSmooth', () => {
  it('preserves endpoints and adds points', () => {
    const pts = [[0, 0], [10, 10], [20, 0]];
    const out = chaikinSmooth(pts, 2);
    expect(out[0]).toEqual([0, 0]);
    expect(out[out.length - 1]).toEqual([20, 0]);
    expect(out.length).toBeGreaterThan(pts.length);
  });

  it('leaves 2-point segments unchanged', () => {
    expect(chaikinSmooth([[0, 0], [5, 5]], 2)).toEqual([[0, 0], [5, 5]]);
  });
});

// ── action -> skeleton ────────────────────────────────────────────────────────

describe('actionToSkeleton', () => {
  it('builds a freedraw skeleton with local points and bbox', () => {
    const sk = actionToSkeleton(makeAction(), region);
    expect(sk.type).toBe('freedraw');
    expect(sk.simulatePressure).toBe(true);
    expect(sk.strokeColor).toBe('#2563eb');
    // Element origin is the min corner; all local points non-negative.
    expect(sk.points.every(([x, y]) => x >= 0 && y >= 0)).toBe(true);
    expect(sk.points.some(([x, y]) => x === 0)).toBe(true);
    expect(sk.width).toBeGreaterThan(0);
    expect(sk.lastCommittedPoint).toEqual(sk.points[sk.points.length - 1]);
  });

  it('builds line and arrow skeletons', () => {
    const line = actionToSkeleton(makeAction({ op: 'line', points: [[0, 0], [30, 20]] }), region);
    expect(line.type).toBe('line');
    expect(line.points[0]).toEqual([0, 0]);
    expect(line.points[1]).toEqual([300, 200]);

    const arrow = actionToSkeleton(makeAction({ op: 'arrow', points: [[0, 0], [30, 20]] }), region);
    expect(arrow.type).toBe('arrow');
    expect(arrow.endArrowhead).toBe('arrow');
  });

  it('builds text skeletons with size mapping', () => {
    const sk = actionToSkeleton(
      makeAction({ op: 'text', points: [[30, 20]], content: 'x^2', size: 'large', color: 'green' }),
      region
    );
    expect(sk).toEqual(expect.objectContaining({
      type: 'text', x: 400, y: 300, text: 'x^2', fontSize: 32, strokeColor: '#16a34a',
    }));
  });

  it('builds ellipse and rectangle skeletons', () => {
    const sk = actionToSkeleton(
      makeAction({ op: 'rect', points: [[10, 10], [20, 18]], color: 'red' }),
      region
    );
    expect(sk.type).toBe('rectangle');
    expect(sk.x).toBe(200);
    expect(sk.y).toBe(200);
    expect(sk.width).toBe(100);
    expect(sk.height).toBe(80);

    const el = actionToSkeleton(makeAction({ op: 'ellipse', points: [[10, 10], [20, 18]] }), region);
    expect(el.type).toBe('ellipse');
  });

  it('returns null for malformed actions', () => {
    expect(actionToSkeleton(null, region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'nope' }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ points: 'x' }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ points: [[1, 2], [3, NaN]] }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'text', points: [[5, 5]], content: null }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'ellipse', points: [[20, 20], [10, 10]] }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'erase' }), region)).toBeNull();
    expect(actionToSkeleton(makeAction(), null)).toBeNull();
  });

  it('falls back to blue / medium for unknown color or size', () => {
    const sk = actionToSkeleton(makeAction({ color: 'purple', size: 'giant' }), region);
    expect(sk.strokeColor).toBe('#2563eb');
    expect(sk.strokeWidth).toBe(2);
  });

  it('maps style to strokeStyle, defaulting to solid', () => {
    const dashed = actionToSkeleton(
      makeAction({ op: 'line', points: [[0, 0], [10, 10]], style: 'dashed' }),
      region
    );
    expect(dashed.strokeStyle).toBe('dashed');
    const plain = actionToSkeleton(makeAction({ op: 'line', points: [[0, 0], [10, 10]] }), region);
    expect(plain.strokeStyle).toBe('solid');
    const bogus = actionToSkeleton(
      makeAction({ op: 'line', points: [[0, 0], [10, 10]], style: 'wavy' }),
      region
    );
    expect(bogus.strokeStyle).toBe('solid');
  });

  it('builds a filled dot for point', () => {
    const sk = actionToSkeleton(makeAction({ op: 'point', points: [[30, 20]], color: 'red' }), region);
    expect(sk.type).toBe('ellipse');
    expect(sk.fillStyle).toBe('solid');
    expect(sk.backgroundColor).toBe('#dc2626');
    // centered on the grid point: (30,20) -> board (400, 300)
    expect(sk.x + sk.width / 2).toBeCloseTo(400);
    expect(sk.y + sk.height / 2).toBeCloseTo(300);
    expect(sk.width).toBeGreaterThan(0);
  });

  it('builds an arc as a sampled polyline (clockwise, y-down)', () => {
    const action = makeAction({ op: 'arc', points: [[30, 20]], radius: 5, angles: [0, 90] });
    const pts = sampleArcPoints(action, region);
    // 0 deg -> (cx + r, cy) = (450, 300); 90 deg -> (cx, cy + r) = (400, 350)
    expect(pts[0][0]).toBeCloseTo(450);
    expect(pts[0][1]).toBeCloseTo(300);
    expect(pts[pts.length - 1][0]).toBeCloseTo(400);
    expect(pts[pts.length - 1][1]).toBeCloseTo(350);
    // <=3 degree steps over a 90 degree sweep
    expect(pts.length).toBeGreaterThanOrEqual(31);

    const sk = actionToSkeleton(action, region);
    expect(sk.type).toBe('line');
    expect(sk.points.length).toBe(pts.length);
    // every sampled point sits on the circle (radius 5 cells = 50 board px)
    for (const [lx, ly] of sk.points) {
      const d = Math.hypot(sk.x + lx - 400, sk.y + ly - 300);
      expect(d).toBeCloseTo(50, 0);
    }
  });

  it('rejects malformed arcs', () => {
    expect(actionToSkeleton(makeAction({ op: 'arc', points: [[30, 20]], radius: null, angles: [0, 90] }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'arc', points: [[30, 20]], radius: 5, angles: null }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'arc', points: [[30, 20]], radius: 5, angles: [0, NaN] }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'arc', points: [[30, 20], [1, 1]], radius: 5, angles: [0, 90] }), region)).toBeNull();
  });

  it('returns null for board-handled ops (math, erase)', () => {
    expect(actionToSkeleton(makeAction({ op: 'math', points: [[5, 5]], content: 'x^2' }), region)).toBeNull();
    expect(actionToSkeleton(makeAction({ op: 'erase', target: 't1' }), region)).toBeNull();
  });
});

// ── board listing ─────────────────────────────────────────────────────────────

describe('elementsToBoardListing', () => {
  const student = { id: 'real-1', type: 'freedraw', x: 100, y: 100, width: 300, height: 200 };
  const tutor = {
    id: 'real-2', type: 'text', x: 400, y: 100, width: 120, height: 25,
    text: '2x + 3 = 11', customData: { source: 'ai' },
  };

  it('aliases student and tutor elements separately with grid boxes', () => {
    const { listing, aliasMap } = elementsToBoardListing([student, tutor], region);
    expect(listing).toHaveLength(2);

    expect(listing[0]).toEqual({
      id: 's1', source: 'student', type: 'freedraw', gridBox: [0, 0, 30, 20], content: null,
    });
    expect(listing[1].id).toBe('t1');
    expect(listing[1].source).toBe('tutor');
    expect(listing[1].content).toBe('2x + 3 = 11');
    expect(aliasMap).toEqual({ s1: 'real-1', t1: 'real-2' });
  });

  it('skips deleted elements', () => {
    const { listing } = elementsToBoardListing([{ ...student, isDeleted: true }], region);
    expect(listing).toEqual([]);
  });

  it('surfaces the LaTeX of AI math images as content', () => {
    const mathImage = {
      id: 'real-3', type: 'image', x: 200, y: 200, width: 80, height: 30,
      customData: { source: 'ai', latex: '\\frac{a}{b}' },
    };
    const { listing } = elementsToBoardListing([mathImage], region);
    expect(listing[0].source).toBe('tutor');
    expect(listing[0].content).toBe('\\frac{a}{b}');
  });
});
