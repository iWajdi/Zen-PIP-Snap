"""Drive a throwaway Zen instance over Marionette: load config.js, open the PiP
player window, shove it around, assert it stays pinned to the remembered edges (with the 10px gap) as its size changes,
and stays put when dropped mid-screen.

  MOZ_REMOTE_ALLOW_SYSTEM_ACCESS=1 Zen.app/Contents/MacOS/zen -profile "$(mktemp -d)" -no-remote -marionette &
  python3 test_snap.py config.js
"""
import json, socket, sys, time

CONFIG = open(sys.argv[1]).read()


class Marionette:
    def __init__(self, port=2828):
        for _ in range(120):
            try:
                self.sock = socket.create_connection(("127.0.0.1", port))
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise SystemExit("marionette never came up")
        self.id = 0
        self.recv()

    def recv(self):
        head = b""
        while not head.endswith(b":"):
            head += self.sock.recv(1)
        n, data = int(head[:-1]), b""
        while len(data) < n:
            data += self.sock.recv(n - len(data))
        return json.loads(data)

    def cmd(self, name, params=None):
        self.id += 1
        payload = json.dumps([0, self.id, name, params or {}]).encode()
        self.sock.sendall(str(len(payload)).encode() + b":" + payload)
        _, _, err, result = self.recv()
        if err:
            raise RuntimeError(err)
        return result


SCRIPT = r"""// Throwaway instance only: drop the config.js copy installed in Zen.app so only the one under test runs.
for (const o of Services.obs.enumerateObservers("chrome-document-loaded")) {
  Services.obs.removeObserver(o, "chrome-document-loaded");
}
""" + CONFIG + r"""
const [resolve] = arguments;
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  Services.prefs.clearUserPref("zen-pip-snap.anchor"); // start from the default, bottom-right
  let win;
  const s = Services.wm.getMostRecentWindow(null).screen;
  const out = { screen: [s.availLeft, s.availTop, s.availWidth, s.availHeight], steps: [] };
  // Firefox opens the player at its own computed spot; left/top here stand in for that.
  const open = async (w, h, left, top) => {
    win?.close();
    win = Services.ww.openWindow(null,
      "chrome://global/content/pictureinpicture/player.xhtml", "_blank",
      `chrome,dialog,titlebar=no,close,resizable,alwaysontop,width=${w},height=${h},left=${left},top=${top}`, null);
    await new Promise(r => win.addEventListener("load", r, { once: true }));
    await sleep(700);
  };
  const corner = (right, bottom) => [
    right ? s.availLeft + s.availWidth - win.outerWidth - 10 : s.availLeft + 10,
    bottom ? s.availTop + s.availHeight - win.outerHeight - 10 : s.availTop + 10,
  ];
  const record = (name, want) => out.steps.push({
    name, want, got: [win.screenX, win.screenY], size: [win.outerWidth, win.outerHeight],
    anchor: Services.prefs.getCharPref("zen-pip-snap.anchor", "(default)"),
  });
  const drop = async (x, y) => {
    win.moveTo(x, y);
    await sleep(100);
    win.dispatchEvent(new win.MouseEvent("mouseup", { bubbles: true }));
    await sleep(600);
  };
  // What Firefox does when the video's aspect ratio changes: resize, then move back to the old top-left.
  const newAspect = async (w, h) => {
    const [x, y] = [win.screenX, win.screenY];
    win.resizeTo(w, h);
    win.moveTo(x, y);
    await sleep(900);
  };
  const fx = Math.round(s.availLeft + s.availWidth * 0.4), fy = Math.round(s.availTop + s.availHeight * 0.3);

  await open(400, 225, 300, 300);
  record("first open, never moved -> bottom-right", corner(true, true));

  await newAspect(300, 400);
  record("portrait video in same window -> still bottom-right", corner(true, true));

  await drop(...corner(true, false).map((v, i) => v + (i ? 15 : -20)));
  record("dropped near top-right -> snaps to top-right", corner(true, false));

  await open(320, 180, 200, 500);
  record("next video, narrower, opened at old left/top -> top-right", corner(true, false));

  await newAspect(500, 281);
  record("wider video in same window -> still top-right", corner(true, false));

  await drop(fx, fy);
  record("dropped mid-screen -> left alone", [fx, fy]);

  await open(300, 400, fx, fy);
  record("next video at remembered free spot -> left alone", [fx, fy]);

  await drop(s.availLeft + s.availWidth - 100, fy);
  record("dropped off right edge -> pinned right, height kept", [corner(true, false)[0], fy]);

  await newAspect(560, 315);
  record("bigger video -> right edge kept, height kept", [corner(true, false)[0], fy]);

  await drop(s.availLeft - 250, s.availTop - 100);
  record("dropped off top-left -> top-left", corner(false, false));

  win.close();
  resolve(out);
})().catch(e => resolve({ error: String(e), stack: e.stack }));
"""

m = Marionette()
m.cmd("WebDriver:NewSession", {"capabilities": {}})
try:
    m.cmd("Marionette:SetContext", {"value": "chrome"})
    out = m.cmd("WebDriver:ExecuteAsyncScript",
                {"script": SCRIPT, "args": [], "sandbox": "system", "newSandbox": True, "scriptTimeout": 30000})["value"]
finally:
    try:
        m.cmd("Marionette:Quit", {"flags": ["eForceQuit"]})
    except Exception:
        pass

print(json.dumps(out, indent=1))
if "error" in out:
    sys.exit(1)
bad = [s for s in out["steps"] if s["want"] != s["got"]]
for s in out["steps"]:
    print(("FAIL " if s in bad else "ok   ") + s["name"], s["got"], "want", s["want"], "| anchor", s["anchor"])
sys.exit(1 if bad else 0)
