import React, { forwardRef, useCallback, useImperativeHandle, useRef, useState } from 'react';
import { Excalidraw, convertToExcalidrawElements, exportToBlob } from '@excalidraw/excalidraw';
import '@excalidraw/excalidraw/index.css';
import Box from '@mui/material/Box';

// Encode a (possibly unicode) SVG string into a data URL safely.
const svgToDataUrl = (svg) => {
  const base64 = btoa(unescape(encodeURIComponent(svg)));
  return `data:image/svg+xml;base64,${base64}`;
};

// Pull an intrinsic size out of an SVG's width/height or viewBox so the image
// element gets a sensible aspect ratio. Falls back to 600x400.
const readSvgSize = (svg) => {
  const widthMatch = svg.match(/\bwidth=["']?([\d.]+)/);
  const heightMatch = svg.match(/\bheight=["']?([\d.]+)/);
  if (widthMatch && heightMatch) {
    return { width: parseFloat(widthMatch[1]), height: parseFloat(heightMatch[1]) };
  }
  const vb = svg.match(/viewBox=["']\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)/);
  if (vb) return { width: parseFloat(vb[1]), height: parseFloat(vb[2]) };
  return { width: 600, height: 400 };
};

const blobToDataUrl = (blob) =>
  new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.readAsDataURL(blob);
  });

// The bottom edge of the current content, so new AI diagrams stack downward.
const contentBottom = (elements) => {
  let bottom = 0;
  for (const el of elements) {
    const elBottom = (el.y || 0) + (el.height || 0);
    if (elBottom > bottom) bottom = elBottom;
  }
  return bottom;
};

/**
 * Excalidraw-backed tutor board. Exposes an imperative API via ref:
 *   capturePng()      -> Promise<string|null>  PNG data URL (null when empty)
 *   injectSvg(svg)    -> void   place an AI diagram below current content
 *   clear()           -> void   wipe the board
 *   hasUserDrawn()    -> bool   has the student added elements since last sync
 *   resetUserDrawn()  -> void   re-baseline after an AI turn
 */
const TutorBoard = forwardRef(function TutorBoard(_props, ref) {
  const [api, setApi] = useState(null);
  // Element count after the last programmatic change (AI injection / sync).
  const baselineCountRef = useRef(0);
  const userDrewRef = useRef(false);

  const handleChange = useCallback((elements) => {
    const live = elements.filter((el) => !el.isDeleted);
    if (live.length > baselineCountRef.current) {
      userDrewRef.current = true;
    }
  }, []);

  const injectSvg = useCallback(
    (svg) => {
      if (!api || !svg) return;

      const { width, height } = readSvgSize(svg);
      // Cap on-board width so large diagrams stay readable; keep aspect ratio.
      const targetWidth = Math.min(width, 600);
      const targetHeight = (height / width) * targetWidth;

      const fileId = `ai-svg-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      api.addFiles([
        { id: fileId, mimeType: 'image/svg+xml', dataURL: svgToDataUrl(svg), created: Date.now() },
      ]);

      const existing = api.getSceneElements();
      const y = existing.length ? contentBottom(existing) + 60 : 100;

      const [imageEl] = convertToExcalidrawElements([
        { type: 'image', fileId, x: 100, y, width: targetWidth, height: targetHeight },
      ]);

      const next = [...existing, imageEl];
      api.updateScene({ elements: next });
      baselineCountRef.current = next.filter((el) => !el.isDeleted).length;
      api.scrollToContent(imageEl, { fitToContent: true, animate: true });
    },
    [api]
  );

  const capturePng = useCallback(async () => {
    if (!api) return null;
    const elements = api.getSceneElements();
    if (!elements.length) return null;
    const blob = await exportToBlob({
      elements,
      files: api.getFiles(),
      mimeType: 'image/jpeg',
      quality: 0.8,
      maxWidthOrHeight: 1000,
      appState: { exportBackground: true, viewBackgroundColor: '#ffffff' },
    });
    return blobToDataUrl(blob);
  }, [api]);

  const clear = useCallback(() => {
    if (!api) return;
    api.updateScene({ elements: [] });
    baselineCountRef.current = 0;
    userDrewRef.current = false;
  }, [api]);

  const resetUserDrawn = useCallback(() => {
    if (!api) return;
    baselineCountRef.current = api.getSceneElements().filter((el) => !el.isDeleted).length;
    userDrewRef.current = false;
  }, [api]);

  useImperativeHandle(
    ref,
    () => ({
      capturePng,
      injectSvg,
      clear,
      hasUserDrawn: () => userDrewRef.current,
      resetUserDrawn,
    }),
    [capturePng, injectSvg, clear, resetUserDrawn]
  );

  return (
    <Box sx={{ flex: 1, minWidth: 0, height: '100%' }}>
      {/* Light board on purpose: the AI generates black-ink SVG diagrams meant
          for a white board, and capturePng exports on a white background for the
          vision pipeline. A light artboard inside the dark app shell keeps both
          the AI's diagrams and the student's dark ink legible. */}
      <Excalidraw theme="light" excalidrawAPI={setApi} onChange={handleChange} />
    </Box>
  );
});

export default TutorBoard;
