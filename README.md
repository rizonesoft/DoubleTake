# DoubleTake

**Look twice. Keep one.** DoubleTake is a free, open source duplicate photo finder for Windows. It matches photos by how they look, not by what they are called, shows each set of copies side by side, and moves the ones you do not want to the Recycle Bin.

> **Status: in development.** There is no release yet. This repository currently holds the design, the architecture and the build plan. The app is being built from them.

## What it will do

- Find byte-identical copies, and copies that were resized, recompressed or lightly edited, using perceptual hashing.
- Read JPEG, PNG, TIFF, WebP, HEIC and camera RAW files.
- Show each group of copies large and side by side, suggest the best one to keep, and let you decide a group with one key.
- Move unwanted copies to the Recycle Bin, never delete them, and put a clean-up back from History.
- Optionally find similar shots (bursts and crops) with a model that runs on your PC.
- Run entirely on your PC. The only network use is a check for a new version and the one-time download of the optional model.

## Where things are

| Path | Contents |
| --- | --- |
| [`design/`](design/) | The interface specification, design tokens, mockups and icon sources |
| [`docs/plans/2026-11-16-doubletake-foundation.md`](docs/plans/2026-11-16-doubletake-foundation.md) | The architecture and the decisions behind it |
| [`todo/implementation-plan.md`](todo/implementation-plan.md) | The build plan |
| [`AGENTS.md`](AGENTS.md) | The working rules for anyone, person or agent, changing the code |

## Technology

C++20 with MSVC, WinUI 3 (Windows App SDK) through C++/WinRT, SQLite, BLAKE3, libheif, LibRaw, ONNX Runtime with DirectML for the optional model, Catch2 for tests, and Inno Setup for the installer. Windows 10 version 1809 or later, x64.

## Licence

DoubleTake is free software under the [GNU General Public License, version 3 or later](LICENSE).
