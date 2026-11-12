"""Drive a throwaway Zen instance over Marionette: load config.js, open the PiP
player window, shove it around, assert it is left alone on-screen and pulled back inside the padded area otherwise.

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
  const win = Services.ww.openWindow(null,
    "chrome://global/content/pictureinpicture/player.xhtml", "_blank",
    "chrome,dialog,titlebar=no,close,resizable,alwaysontop,width=400,height=225,left=300,top=300", null);
  await new Promise(r => win.addEventListener("load", r, { once: true }));
  const s = win.screen, out = { screen: [s.availLeft, s.availTop, s.availWidth, s.availHeight], steps: [] };
  const corner = (right, bottom) => [
    right ? s.availLeft + s.availWidth - win.outerWidth - 10 : s.availLeft + 10,
    bottom ? s.availTop + s.availHeight - win.outerHeight - 10 : s.availTop + 10,
  ];
  const record = (name, want) => out.steps.push({ name, want, got: [win.screenX, win.screenY], size: [win.outerWidth, win.outerHeight] });

  const drop = async (x, y) => {
    win.moveTo(x, y);
    await sleep(100);
    win.dispatchEvent(new win.MouseEvent("mouseup", { bubbles: true }));
    await sleep(600);
  };
  const fx = Math.round(s.availLeft + s.availWidth * 0.4), fy = Math.round(s.availTop + s.availHeight * 0.3);

  await sleep(900);
  record("opened on-screen -> left alone", [300, 300]);

  await drop(s.availLeft + s.availWidth - 100, s.availTop + s.availHeight - 60);
  record("dropped off bottom-right -> padded bottom-right", corner(true, true));

  await drop(s.availLeft - 250, s.availTop - 100);
  record("dropped off top-left -> padded top-left", corner(false, false));

  await drop(fx, fy);
  record("dropped mid-screen -> left alone", [fx, fy]);

  await drop(s.availLeft + s.availWidth - 100, fy);
  record("dropped off right edge -> x pulled in, y kept", [corner(true, false)[0], fy]);

  // Growing while against the right edge must pull it back in without a mouseup.
  win.resizeTo(560, 315);
  await sleep(900);
  record("resized at right edge -> x pulled in, y kept", [corner(true, false)[0], fy]);

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
    print(("FAIL " if s in bad else "ok   ") + s["name"], s["got"], "want", s["want"])
sys.exit(1 if bad else 0)
