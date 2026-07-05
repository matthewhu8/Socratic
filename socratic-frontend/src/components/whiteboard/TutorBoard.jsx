import React, { forwardRef, useCallback, useImperativeHandle, useRef, useState } from 'react';
import {
  CaptureUpdateAction,
  Excalidraw,
  convertToExcalidrawElements,
  exportToBlob,
} from '@excalidraw/excalidraw';
import '@excalidraw/excalidraw/index.css';
import Box from '@mui/material/Box';
import {
  COLOR_HEX,
  MATH_SCALE,
  actionToSkeleton,
  computeBoardRegion,
  elementsToBoardListing,
  gridToBoard,
  stampGrid,
} from './drawProtocol';

// Encode a (possibly unicode) SVG string into a data URL safely.
const svgToDataUrl = (svg) => {
  const base64 = btoa(unescape(encodeURIComponent(svg)));
  return `data:image/svg+xml;base64,${base64}`;
};

// Lazy-load the MathJax tex-svg bundle once, configured for self-contained SVG
// output (fontCache: 'none' inlines glyph paths so the SVG renders inside <img>).
let mathJaxPromise = null;
const loadMathJax = () => {
  if (!mathJaxPromise) {
    window.MathJax = {
      tex: {},
      svg: { fontCache: 'none' },
      startup: { typeset: false },
    };
    mathJaxPromise = import('mathjax/es5/tex-svg')
      .then(() => window.MathJax.startup.promise)
      .then(() => window.MathJax);
  }
  return mathJaxPromise;
};

// MathJax sizes its SVG in ex units (~8px at the default 16px base font).
const EX_TO_PX = 8;

const latexToSvg = async (latex, colorHex) => {
  const MathJax = await loadMathJax();
  const container = MathJax.tex2svg(latex, { display: true });
  const svgEl = container.querySelector('svg');
  if (!svgEl) throw new Error('MathJax produced no svg');
  // MathJax renders bad TeX as an error box instead of throwing — treat it as a
  // failure so the caller's plain-text fallback shows the raw LaTeX instead.
  if (svgEl.querySelector('[data-mjx-error], merror')) {
    throw new Error(`MathJax could not parse: ${latex}`);
  }
  svgEl.setAttribute('color', colorHex); // MathJax paths use currentColor
  const width = parseFloat(svgEl.getAttribute('width')) * EX_TO_PX;
  const height = parseFloat(svgEl.getAttribute('height')) * EX_TO_PX;
  return { svg: svgEl.outerHTML, width, height };
};

const blobToStampedDataUrl = async (blob) => {
  const bitmap = await createImageBitmap(blob);
  const canvas = document.createElement('canvas');
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(bitmap, 0, 0);
  stampGrid(canvas);
  return canvas.toDataURL('image/jpeg', 0.8);
};

// Invisible 1px corner markers pin exportToBlob's bounds to exactly boardRegion
// (the export otherwise crops to the content bbox). Never added to the scene.
const regionMarkers = (region) =>
  convertToExcalidrawElements([
    { type: 'rectangle', x: region.x, y: region.y, width: 1, height: 1, opacity: 0 },
    {
      type: 'rectangle',
      x: region.x + region.width - 1,
      y: region.y + region.height - 1,
      width: 1,
      height: 1,
      opacity: 0,
    },
  ]);

/**
 * Excalidraw-backed tutor board. Exposes an imperative API via ref:
 *   captureBoardContext() -> Promise<{png, region, elements}|null>
 *       the grid-stamped screenshot + coordinate frame + symbolic listing that
 *       the AI reads (draw-protocol spec §1/§2). Pins the frame the AI's draw
 *       actions will map through this turn.
 *   beginAiTurn()         -> void   reset the per-turn first-action flag
 *   applyDrawAction(a)    -> void   render one wire action as a native element
 *   clear()               -> void   wipe the board
 *   hasUserDrawn()        -> bool   has the student added elements since last sync
 *   resetUserDrawn()      -> void   re-baseline after an AI turn
 */
const TutorBoard = forwardRef(function TutorBoard(_props, ref) {
  const [api, setApi] = useState(null);
  // Element count after the last programmatic change (AI injection / sync).
  const baselineCountRef = useRef(0);
  const userDrewRef = useRef(false);
  // Pinned per turn at capture time so read and write share one frame.
  const drawRegionRef = useRef(null);
  const aliasMapRef = useRef({});
  const firstActionRef = useRef(true);
  const drawQueueRef = useRef(Promise.resolve());

  const handleChange = useCallback((elements) => {
    const live = elements.filter((el) => !el.isDeleted);
    if (live.length > baselineCountRef.current) {
      userDrewRef.current = true;
    }
  }, []);

  const captureBoardContext = useCallback(async () => {
    if (!api) return null;
    const elements = api.getSceneElements();
    const region = computeBoardRegion(elements);
    const { listing, aliasMap } = elementsToBoardListing(elements, region);
    drawRegionRef.current = region;
    aliasMapRef.current = aliasMap;

    const blob = await exportToBlob({
      elements: [...elements, ...regionMarkers(region)],
      files: api.getFiles(),
      mimeType: 'image/png',
      maxWidthOrHeight: 1200,
      exportPadding: 0,
      appState: { exportBackground: true, viewBackgroundColor: '#ffffff' },
    });
    const png = await blobToStampedDataUrl(blob);
    return { png, region, elements: listing };
  }, [api]);

  const beginAiTurn = useCallback(() => {
    firstActionRef.current = true;
  }, []);

  const eraseTutorElement = useCallback(
    (targetAlias) => {
      const realId = aliasMapRef.current[targetAlias];
      if (!realId) return;
      const existing = api.getSceneElements();
      const target = existing.find((el) => el.id === realId);
      // Ownership check independent of the backend's: student ink is never erasable.
      if (!target || target.customData?.source !== 'ai') {
        console.warn('[TutorBoard] refused erase of non-tutor element', targetAlias);
        return;
      }
      const next = existing.filter((el) => el.id !== realId);
      api.updateScene({ elements: next, captureUpdate: CaptureUpdateAction.NEVER });
      baselineCountRef.current = next.filter((el) => !el.isDeleted).length;
    },
    [api]
  );

  const appendAiElement = useCallback(
    (element) => {
      const next = [...api.getSceneElements(), element];
      // NEVER: AI marks must not pollute the student's undo stack.
      api.updateScene({ elements: next, captureUpdate: CaptureUpdateAction.NEVER });
      baselineCountRef.current = next.filter((el) => !el.isDeleted).length;

      if (firstActionRef.current) {
        firstActionRef.current = false;
        // Fit the whole scene, not the single new element — a lone thin mark has a
        // near-degenerate bbox and fitToContent would zoom absurdly (or NaN).
        api.scrollToContent(next, { fitToContent: true, animate: true });
      }
    },
    [api]
  );

  // Render a `math` action: LaTeX -> self-contained MathJax SVG -> image element.
  // On any render failure, fall back to a plain text element with the raw LaTeX —
  // the mark is never silently dropped.
  const applyMathAction = useCallback(
    async (action) => {
      const region = drawRegionRef.current;
      const [x, y] = gridToBoard(action.points[0], region);
      const scale = MATH_SCALE[action.size] || MATH_SCALE.medium;
      try {
        const colorHex = COLOR_HEX[action.color] || COLOR_HEX.blue;
        const { svg, width, height } = await latexToSvg(action.content, colorHex);
        if (!Number.isFinite(width) || !Number.isFinite(height)) {
          throw new Error('MathJax svg has non-finite size');
        }
        const fileId = `ai-math-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        api.addFiles([
          { id: fileId, mimeType: 'image/svg+xml', dataURL: svgToDataUrl(svg), created: Date.now() },
        ]);
        const [converted] = convertToExcalidrawElements([
          { type: 'image', fileId, x, y, width: width * scale, height: height * scale },
        ]);
        appendAiElement({ ...converted, customData: { source: 'ai', latex: action.content } });
      } catch (err) {
        console.warn('[TutorBoard] math render failed, falling back to text', err);
        const skeleton = actionToSkeleton({ ...action, op: 'text' }, region);
        if (!skeleton) return;
        const [converted] = convertToExcalidrawElements([skeleton]);
        appendAiElement({ ...converted, customData: { source: 'ai', latex: action.content } });
      }
    },
    [api, appendAiElement]
  );

  const applyOneAction = useCallback(
    async (action) => {
      if (!api || !action) return;
      if (action.op === 'erase') {
        eraseTutorElement(action.target);
        return;
      }
      if (action.op === 'math') {
        await applyMathAction(action);
        return;
      }

      const skeleton = actionToSkeleton(action, drawRegionRef.current);
      if (!skeleton) {
        console.warn('[TutorBoard] skipped malformed draw action', action);
        return;
      }
      const [converted] = convertToExcalidrawElements([skeleton]);
      appendAiElement({ ...converted, customData: { source: 'ai' } });
    },
    [api, eraseTutorElement, applyMathAction, appendAiElement]
  );

  // Serialize actions through a promise chain so an async math render can't be
  // overtaken by the next (synchronous) action — board z-order matches wire order.
  const applyDrawAction = useCallback(
    (action) => {
      drawQueueRef.current = drawQueueRef.current
        .then(() => applyOneAction(action))
        .catch((err) => console.warn('[TutorBoard] draw action failed', err));
    },
    [applyOneAction]
  );

  const clear = useCallback(() => {
    if (!api) return;
    api.updateScene({ elements: [] });
    baselineCountRef.current = 0;
    userDrewRef.current = false;
    drawRegionRef.current = null;
    aliasMapRef.current = {};
  }, [api]);

  const resetUserDrawn = useCallback(() => {
    if (!api) return;
    baselineCountRef.current = api.getSceneElements().filter((el) => !el.isDeleted).length;
    userDrewRef.current = false;
  }, [api]);

  useImperativeHandle(
    ref,
    () => ({
      captureBoardContext,
      beginAiTurn,
      applyDrawAction,
      clear,
      hasUserDrawn: () => userDrewRef.current,
      resetUserDrawn,
    }),
    [captureBoardContext, beginAiTurn, applyDrawAction, clear, resetUserDrawn]
  );

  // Dev-only hook for browser-driven tests (webapp-testing skill): lets Playwright
  // exercise the draw pipeline without an LLM round-trip. Stripped from prod builds.
  if (process.env.NODE_ENV !== 'production') {
    window.__tutorBoardDebug = { api, captureBoardContext, beginAiTurn, applyDrawAction };
  }

  return (
    <Box sx={{ flex: 1, minWidth: 0, height: '100%' }}>
      {/* Light board on purpose: the AI reads a white-background capture and draws
          in the tutor palette (blue/green/red); student ink stays dark. */}
      <Excalidraw theme="light" excalidrawAPI={setApi} onChange={handleChange} />
    </Box>
  );
});

export default TutorBoard;
