# Pytuix

A lightweight Thiele-Small loudspeaker parameter solver and SPL response simulator, built in Python because [VituixCAD](https://kimmosaunisto.net/Software/VituixCAD/) doesn't run on macOS.

Pytuix (Python + VituixCAD) lets you enter whatever Thiele-Small parameters you have for a driver, solve for the ones you're missing, and plot the predicted closed-box SPL response, with support for comparing multiple driver systems side by side.


## Why this exists

Loudspeaker development involves constantly comparing predicted driver response across design iterations; a baseline system against a proposed change, or a supplier's stated parameters against measured ones. VituixCAD is the industry-standard tool for this, but it's Windows-only. Pytuix reimplements the core Thiele-Small math and closed-box transfer function so that comparison can happen without leaving macOS.

## Features

- **Parameter solver:** enter any subset of Thiele-Small parameters (Vas, fs, Qts, Qes, Qms, Cms, Mms, Rms, Bl, Sd, Re, n0) and Pytuix iteratively derives the rest from known physical relationships, the same way a driver datasheet rarely gives you every value at once.
- **Multi-system comparison:** model up to 4 driver systems simultaneously, each with an independent driver count (for series/parallel arrays), and overlay their predicted SPL curves on one plot.
- **Interactive plot:** hover over any curve to see exact frequency/SPL readouts; live-updating via a separate plot window.
- **File import:** load parameters from a whitespace-separated `.txt` file instead of typing them in by hand.
- **Keyboard scaling:** arrow keys nudge a focused parameter up/down and instantly regenerate the plot, useful for quick sensitivity checks.

## Installation

Requires Python 3.9+.

```bash
pip install matplotlib
```

`tkinter` ships with most standard Python installations. On some Linux distributions you may need to install it separately (e.g. `sudo apt install python3-tk`).

## Usage

```bash
python Pytuix.py
```

1. Choose how many systems you want to compare (1–4) from the dropdown.
2. Enter known Thiele-Small parameters for each system, or click **Load File** to import them from a `.txt` file.
3. Click **Auto Calculate** once enough parameters are known to solve for the rest — the button enables automatically when a solve is possible.
4. Click **Generate Plot** to view the predicted SPL response for each system in a separate window.

## How it works

The core solver (`TS_Parameters.solve()`) is a simple iterative constraint resolver: it repeatedly scans for any parameter it can compute from ones that are already known (e.g. deriving `Vas` from `Sd` and `Cms`, or `Qts` from `Qes` and `Qms`), and loops until no further values change. This mirrors how these parameters actually relate to each other physically — most are interdependent, so partial data is usually enough to fill in the rest.

The SPL transfer function models a driver in a sealed enclosure using the standard closed-box high-pass response, with the Small/Dickason reference efficiency formula (`112.2 + 10·log10(n0)`) for baseline sensitivity, corrected for enclosure volume, drive power, and acoustic coupling gain across multiple drivers.

## Limitations

- **Sealed enclosures only.** Vented (ported) box modeling isn't implemented.


## Roadmap

- [ ] Vented box (Helmholtz-tuned) transfer function
- [ ] Unit tests for `TS_Parameters.solve()`
- [ ] Refactor UI state out of module-level globals into an `App` class
- [ ] Export plotted data to CSV

## Author

Built by Nicolas Adler, Audio Systems Engineer.
