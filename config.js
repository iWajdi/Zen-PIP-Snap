// Zen PiP, Arc-style: remembers which screen edges you put it against and keeps a MARGIN gap from them. (Autoconfig ignores this first line; keep it a comment.)
try {
  const MARGIN = 10; // gap between the PiP window and the screen edge, px (measured from Arc)
  const SNAP = 40; // drop it within this many px of an edge and it snaps to that edge; 0 turns this off
  const DURATION = 180; // snap animation, ms
  const PREF = "zen-pip-snap.anchor"; // remembered edges as "x,y", each "start", "end" or "free"
  const DEFAULT_ANCHOR = "end,end"; // before you first move it: bottom-right, where Firefox opens PiP

  // Cc/Ci rather than Services: guaranteed to exist in the autoconfig scope.
  const prefs = Cc["@mozilla.org/preferences-service;1"].getService(Ci.nsIPrefBranch);

  Cc["@mozilla.org/observer-service;1"].getService(Ci.nsIObserverService).addObserver(doc => {
    if (doc.documentURI != "chrome://global/content/pictureinpicture/player.xhtml") {
      return;
    }
    const win = doc.defaultView;
    let anim, debounce;

    // learn: the user just dropped the window, so where it landed becomes the remembered spot.
    const place = (learn, animate) => {
      win.clearInterval(anim);
      if (win.fullScreen || doc.fullscreenElement) {
        return;
      }
      const s = win.screen;
      // Per axis: [current position, padded start, padded end].
      const axes = [
        [win.screenX, s.availLeft + MARGIN, s.availLeft + s.availWidth - win.outerWidth - MARGIN],
        [win.screenY, s.availTop + MARGIN, s.availTop + s.availHeight - win.outerHeight - MARGIN],
      ];
      let anchors = prefs.getCharPref(PREF, DEFAULT_ANCHOR).split(",");
      if (learn) {
        anchors = axes.map(([pos, lo, hi]) => (pos <= lo + SNAP ? "start" : pos >= hi - SNAP ? "end" : "free"));
        prefs.setCharPref(PREF, anchors.join(","));
      }
      // Anchored axes go to their padded edge whatever the window's size; free ones stay put, kept on screen.
      const [[x0], [y0]] = axes;
      const [x1, y1] = axes.map(([pos, lo, hi], i) =>
        Math.round(anchors[i] == "start" ? lo : anchors[i] == "end" ? hi : Math.max(lo, Math.min(pos, hi)))
      );
      if (x0 == x1 && y0 == y1) {
        return;
      }
      if (!animate) {
        win.moveTo(x1, y1);
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

    win.addEventListener("mousedown", () => win.clearInterval(anim));
    win.addEventListener("mouseup", () => win.setTimeout(() => place(true, true))); // after Zen's own handlers
    // A new video's aspect ratio, or a native edge-resize (which gives no mouseup), arrives as a resize.
    // Firefox moves the window right after resizing it, so wait for both to settle.
    // ponytail: fixed 250ms settle; listen for Firefox's own move instead if it ever lands later than that.
    win.addEventListener("resize", () => {
      win.clearTimeout(debounce);
      debounce = win.setTimeout(() => place(false, true), 250);
    });
    win.setTimeout(() => place(false, false)); // on open: jump straight to the remembered spot
  }, "chrome-document-loaded");
} catch (e) {
  Components.utils.reportError(e);
}
