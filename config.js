// Zen PiP: place it anywhere, but it never sits off-screen or tighter than MARGIN to an edge. (Autoconfig ignores this first line; keep it a comment.)
try {
  const MARGIN = 10; // gap between the PiP window and the screen edge, px (measured from Arc)
  const DURATION = 180; // snap animation, ms

  // Cc/Ci rather than Services: guaranteed to exist in the autoconfig scope.
  Cc["@mozilla.org/observer-service;1"].getService(Ci.nsIObserverService).addObserver(doc => {
    if (doc.documentURI != "chrome://global/content/pictureinpicture/player.xhtml") {
      return;
    }
    const win = doc.defaultView;
    let anim, debounce;

    const snap = () => {
      win.clearInterval(anim);
      if (win.fullScreen || doc.fullscreenElement) {
        return;
      }
      // Free placement; each axis is only pulled back inside the padded screen area.
      const clamp = (pos, size, min, avail) =>
        Math.round(Math.max(min + MARGIN, Math.min(pos, min + avail - size - MARGIN)));
      const s = win.screen;
      const x0 = win.screenX;
      const y0 = win.screenY;
      const x1 = clamp(x0, win.outerWidth, s.availLeft, s.availWidth);
      const y1 = clamp(y0, win.outerHeight, s.availTop, s.availHeight);
      if (x0 == x1 && y0 == y1) {
        return;
      }
      const start = win.performance.now();
      // setInterval, not requestAnimationFrame: rAF stalls while the window is off-screen.
      anim = win.setInterval(() => {
        const t = Math.min(1, (win.performance.now() - start) / DURATION);
        const ease = 1 - (1 - t) ** 3;
        win.moveTo(Math.round(x0 + (x1 - x0) * ease), Math.round(y0 + (y1 - y0) * ease));
        if (t == 1) {
          win.clearInterval(anim);
        }
      }, 8);
    };
    // ponytail: native edge-resize gives no mouseup, so resize settles on a 250ms pause.
    const snapSoon = () => {
      win.clearTimeout(debounce);
      debounce = win.setTimeout(snap, 250);
    };

    win.addEventListener("mousedown", () => win.clearInterval(anim));
    win.addEventListener("mouseup", () => win.setTimeout(snap)); // after Zen's own handlers
    win.addEventListener("resize", snapSoon);
    snapSoon();
  }, "chrome-document-loaded");
} catch (e) {
  Components.utils.reportError(e);
}
