---
name: webapp-testing
description: Toolkit for interacting with and testing local web applications using Playwright. Use to verify frontend functionality, debug UI behavior, capture browser screenshots, and view browser console logs. Apply to the socratic-frontend React app when confirming a change works in the real UI.
license: Adapted from anthropics/skills (https://github.com/anthropics/skills). See repo for full terms.
---

# Web Application Testing

> Vendored/adapted from anthropics/skills. Use it to verify changes to the Socratic React app
> (`socratic-frontend/`, dev server on http://localhost:3000) against a real browser rather than
> guessing. Backend must be running on :8000 for authenticated flows.

## Overview
Test local web apps through Python Playwright scripts. Decide first whether you can inspect static
HTML directly or must drive the running dev server.

## Core practices
- Use **headless Chromium**.
- On dynamic (JS) apps, always `await page.wait_for_load_state('networkidle')` before inspecting the
  DOM, so React has finished rendering.
- Prefer descriptive selectors: `text=`, `role=`, CSS, IDs.
- "Reconnaissance, then action": inspect what's on the page before clicking/typing.
- Capture `console` messages and screenshots to debug failures.

## Setup
```bash
pip install playwright
python -m playwright install chromium
```

## Minimal pattern
```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda m: print("console:", m.type, m.text))
        await page.goto("http://localhost:3000/student/auth")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="auth.png", full_page=True)
        # e.g. await page.fill("input[type=email]", "test@example.com")
        await browser.close()

asyncio.run(main())
```

## Socratic-specific tips
- Most routes are behind `ProtectedRoute` (`/student/*`). To test them you'll need a valid token in
  `localStorage` (`accessToken`/`refreshToken`) — either log in via the UI or inject tokens with
  `page.add_init_script(...)` before navigating.
- Math is rendered with KaTeX; assert on rendered text/`.katex` nodes, not raw `$...$`.
- The AI tutor canvas and QR grading use polling — wait/retry rather than expecting instant updates.
- For pure-static checks, you can load built HTML via a `file://` URL after `npm run build`.
