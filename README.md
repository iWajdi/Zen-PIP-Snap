# Arc-style Picture-in-Picture for Zen: stays on screen, keeps a gap at the edges

In Arc you can't leave the PiP window hanging off the screen. Drop it past an edge and it glides back, and it always keeps a small gap from the screen edge and the Dock. Zen's PiP goes wherever you drop it, so it can end up half off-screen or pressed right against an edge. I wanted Arc's behaviour in Zen, so I put together a small script for it.

With the script installed:

- You can still put the window anywhere. If you drop it on screen, it stays where you left it.
- If you drop it past an edge, it glides back in and stops 10px from that edge.
- If you drop it past a corner, it ends up in the corner with the same 10px gap.
- If you resize it so that it would overflow the screen, it moves back inside.
- It accounts for the menu bar and the Dock, and it leaves fullscreen PiP alone.

You don't have to hold a key. Zen does have a built-in snap (hold ⌘ while dragging, or Ctrl on Windows and Linux, and the window jumps to a corner), but that one puts the window flush against the edge and does nothing for a window that is already off-screen.

## How it works

The script uses Firefox's AutoConfig: a `config.js` in the application folder that Zen runs at startup. It waits for the PiP player window to open. Each time you release the mouse or finish resizing, it checks whether the window sits outside the screen area minus the 10px gap, and if it does, moves it back with a short ease-out animation. None of Zen's own files are patched or replaced.

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

There are two constants at the top of `config.js`. `MARGIN` is the gap from the screen edge in pixels (10 is about what Arc uses), and `DURATION` is the length of the glide in milliseconds. Restart Zen after you change them.

## Uninstall

Delete `config.js` and `defaults/pref/config-prefs.js`, then restart Zen.

## Test

`test_snap.py` drives a throwaway Zen profile over Marionette, moves the PiP window around, and checks where it ends up. The command to run it is at the top of the file.

## Caveats

- I have only tested this on macOS, with Zen 1.24.2b.
- `config-prefs.js` turns off the AutoConfig sandbox, so `config.js` runs with full browser privileges. userChrome.js loaders use the same mechanism. The script is about 50 lines, so read it before you install it.
- On macOS, adding files inside `Zen.app` makes `codesign --verify` fail for the bundle. Zen still runs normally.
- A Zen update may remove the files. If the behaviour stops after an update, copy them in again.

I'd like to see this as a built-in option, since the PiP player already contains corner-snapping code.
