# Arc-style Picture-in-Picture for Zen: stays on screen, keeps a gap at the edges

In Arc you can't leave the PiP window hanging off the screen. Drop it past an edge and it glides back, and it always keeps a small gap from the screen edge and the Dock. It also remembers where you put it: if you parked it in the top-right corner, the next video opens there too, with the same gap, whatever its aspect ratio.

Zen's PiP goes wherever you drop it, so it can end up half off-screen or pressed right against an edge. And because Firefox remembers the window's top-left corner rather than the edge it was against, a video with a different aspect ratio opens with a gap on the right, or flush against it. I wanted Arc's behaviour in Zen, so I put together a small script for it.

With the script installed:

- Until you move it, the window sits in the bottom-right corner, 10px from the edges.
- If you drop it near an edge (within 40px) or past it, it glides to that edge and stops 10px from it. Near a corner, it goes into the corner.
- It remembers the edges you left it against. When the next video opens, or the video changes size, it stays against those edges with the same gap.
- You can still put the window anywhere. If you drop it in the middle of the screen, it stays there, and the next video opens in the same spot.
- It accounts for the menu bar and the Dock, and it leaves fullscreen PiP alone.

You don't have to hold a key. Zen does have a built-in snap (hold ⌘ while dragging, or Ctrl on Windows and Linux, and the window jumps to a corner), but that one puts the window flush against the edge and does nothing for a window that is already off-screen.

## How it works

The script uses Firefox's AutoConfig: a `config.js` in the application folder that Zen runs at startup. It waits for the PiP player window to open. When you release the mouse after moving the window, it works out which edges the window is against (left, right, top, bottom, or none) and saves that as a pref. Whenever a PiP window opens or changes size, it moves the window back against the saved edges, 10px in, with a short ease-out animation. On an edge with nothing saved, it only makes sure the window isn't off-screen. None of Zen's own files are patched or replaced.

## Install

You need two files from this repo: [`config.js`](config.js) and [`defaults/pref/config-prefs.js`](defaults/pref/config-prefs.js). The quickest way to get them is Code, then Download ZIP, on the repo page.

### macOS

1. Quit Zen.
2. In Finder, right-click Zen in Applications, choose Show Package Contents, and open `Contents/Resources`.
3. Copy `config.js` and the `defaults` folder into `Resources`.
4. Open Zen again.

Do this in Finder. Copying from a terminal fails with "Operation not permitted" unless the terminal app has the App Management permission (System Settings, Privacy & Security).

### Windows (untested)

The same two files go in Zen's install folder, the one that contains `zen.exe`. Put `config.js` next to `zen.exe` and `config-prefs.js` in `defaults\pref\`. You will probably need admin rights.

### Linux (untested)

The layout is the same, in the directory that contains the `zen` binary. I expect it to fail on Wayland, where a window can't read or set its own position. X11 should be fine. Flatpak installs are read-only, so these steps don't work there.

### If you already use Sine or fx-autoconfig

You already have a `config.js`, so don't overwrite it. Pasting the script at the end of your existing `config.js` and skipping `config-prefs.js` should work, but I haven't tried it.

## Settings

These constants are at the top of `config.js`:

- `MARGIN`: the gap from the screen edge in pixels. 10 is about what Arc uses.
- `SNAP`: how close to an edge you have to drop the window for it to snap there, in pixels. Set it to 0 if you only want it to snap when you drop it past the edge.
- `DURATION`: the length of the glide in milliseconds.
- `DEFAULT_ANCHOR`: where the window goes before you've moved it. `"end,end"` is bottom-right; `"start"` is left or top.

Restart Zen after you change them.

The remembered edges are stored in the `zen-pip-snap.anchor` pref, which you can see in `about:config`. Resetting it puts the window back to the default corner.

## Uninstall

Delete `config.js` and `defaults/pref/config-prefs.js`, then restart Zen. The `zen-pip-snap.anchor` pref stays behind but does nothing; delete it in `about:config` if you like.

## Test

`test_snap.py` drives a throwaway Zen profile over Marionette, moves the PiP window around, and checks where it ends up. The command to run it is at the top of the file.

## Caveats

- I have only tested this on macOS, with Zen 1.24.2b.
- `config-prefs.js` turns off the AutoConfig sandbox, so `config.js` runs with full browser privileges. userChrome.js loaders use the same mechanism. The script is about 50 lines, so read it before you install it.
- On macOS, adding files inside `Zen.app` makes `codesign --verify` fail for the bundle. Zen still runs normally.
- A Zen update may remove the files. If the behaviour stops after an update, copy them in again.

I'd like to see this as a built-in option, since the PiP player already contains corner-snapping code.
