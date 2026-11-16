# DoubleTake foundation plan

Written 2026-11-16. This is the architecture the TODO tree executes. The interface is specified in [`design/SPEC.md`](../../design/SPEC.md); this file covers everything behind it. Sections are numbered so TODO items can cite them.

## 1. Product

DoubleTake finds duplicate photos by how they look. The user picks folders, the app reads every photo once, groups the copies, and shows each group side by side. The user keeps one and the rest go to the Recycle Bin. It is a free Windows desktop app, open source under GPL-3.0, and everything runs on the user's PC.

## 2. Decisions

Each was made by the owner on 2026-11-16 unless marked otherwise. Reversing one means rewriting the sections that cite it.

| Id | Decision |
| --- | --- |
| D1 | Windows only, x64, Windows 10 version 1809 and later. No other platform is planned. |
| D2 | C++20 with MSVC. All projects are MSBuild projects in one solution. No C#, no Rust. |
| D3 | The interface is WinUI 3 (Windows App SDK) in C++/WinRT, unpackaged and self-contained. |
| D4 | Libraries come from vcpkg in manifest mode (BLAKE3, SQLite, libheif, LibRaw, Catch2) and from NuGet (Windows App SDK, C++/WinRT, ONNX Runtime with DirectML). |
| D5 | Matching is perceptual hashing (our own dHash and pHash). ML similarity is an optional setting, off by default, and its model is downloaded only when the user turns it on. |
| D6 | Unwanted copies go to the Recycle Bin through `IFileOperation`. The app never deletes a file outright. |
| D7 | Updates are a notice only. The app reads a small version file and opens the download page in the browser. It never downloads or installs an update, and is never distributed through the Microsoft Store. |
| D8 | Licence GPL-3.0-or-later. Every dependency must be compatible with it. |
| D9 | The installer is built with Inno Setup and installs per user, with no administrator prompt. |
| D10 | Code signing is deferred. Nothing in the plan may wait on a certificate. |
| D11 | The design direction is Darkroom, dark only (`design/SPEC.md`). |
| D12 | (Plan author) The version file is `version.json` at the root of the GitHub repository's main branch, read from `raw.githubusercontent.com`. Its `url` field names the download page, so the owner can point it at the website without a new build. |
| D13 | (Plan author) Interface logic lives in a plain C++ library with no XAML dependency, so it is unit tested without a window. |

## 3. Repository layout

| Path | Contents |
| --- | --- |
| `DoubleTake.sln` | The one solution |
| `Directory.Build.props`, `Directory.Build.targets` | Shared compiler settings: C++20, `/W4 /WX`, `/permissive-`, x64, output under `build/` |
| `version.props` | The one place the version number is written |
| `vcpkg.json`, `vcpkg-configuration.json` | The vcpkg manifest and its pinned baseline |
| `src/engine/` | `doubletake-engine`, a static library: scan, decode, hash, match, index, recycle, restore |
| `src/appcore/` | `doubletake-appcore`, a static library: view models, settings, update check, text formatting |
| `src/app/` | `DoubleTake`, the WinUI 3 executable: XAML pages and the thin code that binds them to `appcore` |
| `src/cli/` | `doubletake-cli`, a console program over the engine, used by tests and never installed |
| `tests/engine/`, `tests/appcore/` | Catch2 test programs |
| `tests/ui/` | `doubletake-uitests`, UI Automation tests that drive the running app |
| `tests/fixtures/` | The script that generates the photo fixtures, and the few committed sample files it cannot generate |
| `resources/` | Generated icons, fonts, the string resources and installer images |
| `installer/` | The Inno Setup script |
| `scripts/` | Build, check, capture and brand scripts, beside the Conclave kit scripts |
| `design/` | The interface specification, tokens, mockups and icon sources |
| `todo/`, `docs/` | The plan and its documents |

## 4. Build and tools

- Visual Studio 2026 with the C++ desktop workload, toolset `v145`, Windows SDK `10.0.26100.0`. `scripts/build.ps1` finds the installation with `vswhere` and never assumes a path.
- vcpkg is the copy bundled with Visual Studio (`VC\vcpkg\vcpkg.exe`), in manifest mode with MSBuild integration, triplet `x64-windows-static-md`.
- NuGet packages are restored by `nuget restore DoubleTake.sln` and pinned in `packages.config` files.
- `pwsh scripts/build.ps1 [-Configuration Debug|Release]` restores and builds the solution. `pwsh scripts/check.ps1` builds Debug, runs every test program, and runs the plan checks; it is the one command that must pass before a section is reviewed. Full builds and full test runs go through `bosun run --` when `bosun` is installed.
- `scripts/gen-compile-commands.py` writes `build/compile_commands.json` for clangd from the MSBuild projects.
- Inno Setup's compiler is found through its registry key or its default folder, never assumed to be on `PATH`.
- Continuous integration is one GitHub Actions workflow on a Windows runner: restore, build, test, plan checks.

## 5. Engine

The engine is plain C++20 over Win32 and COM. It has no dependency on XAML or WinRT projections, and every public function takes a cancel token and reports through return values, never by throwing across the library boundary.

### 5.1 Scan

- Walk each folder with `std::filesystem::recursive_directory_iterator`, skipping reparse points, and hidden and system folders unless the setting allows them. A folder that cannot be opened is recorded and the walk continues.
- A file is a photo when its extension is in the format table (5.2). Files below the minimum pixel size are left out after decoding.
- Work runs on a pool of `hardware_concurrency - 1` threads (at least 1). Progress is published at most ten times a second.
- A file whose path, size and modified time match its index row is not read again.

### 5.2 Decode

| Formats | Decoder |
| --- | --- |
| JPEG, PNG, BMP, GIF (first frame), TIFF, WebP | Windows Imaging Component |
| HEIC, HEIF, AVIF | libheif |
| CR2, CR3, NEF, ARW, DNG, RAF, ORF, RW2 | LibRaw, using the embedded preview when it is at least 1024 wide, else a half-size decode |

Every decoder returns 8-bit BGRA with the EXIF orientation already applied, at a requested longest side, so hashing asks for a small image and the compare panes ask for a large one. EXIF capture date and camera model are read at the same time.

### 5.3 Hashes

- **Exact:** BLAKE3 of the file bytes, computed only for files that share a size with another file.
- **dHash:** reduce to 9 x 8 grey by area averaging; each bit is whether a pixel is brighter than its right neighbour. 64 bits.
- **pHash:** reduce to 32 x 32 grey, take the two-dimensional DCT-II and keep the top-left 8 x 8 block of coefficients; each bit is whether a coefficient is above the median of the block, with the DC term left out of the median. 64 bits.
- Grey is Rec. 601 luma of the sRGB values. Both hashes must give the same value on every machine for the same pixels, so the DCT uses a fixed table and no fast-math.

### 5.4 Matching

- Files with the same BLAKE3 are an exact pair.
- Other pairs come from a BK-tree over pHash with Hamming distance. A candidate within the pHash limit is confirmed by the dHash limit.

| Closeness | pHash limit | dHash limit | Aspect ratio |
| --- | --- | --- | --- |
| Exact | exact pairs only | | |
| Close | 6 | 10 | within 2% |
| Loose | 12 | 18 | any |

- These limits are the starting values. The fixture test (section 8) is the authority: every labelled duplicate found, and no pair labelled different grouped, at Close. A limit changes only with that test.
- Groups are the connected sets of confirmed pairs (union-find).
- Kind, judged against the keeper: `Exact` (same bytes), `Recompressed` (same pixel size, different bytes), `Resized` (different pixel size, same aspect), `Edited` (anything else found by hashing), `Similar` (found only by the model, section 7). A group's kind is the loosest of its members'.
- Likeness is `round(100 * (64 - pHash distance) / 64)` between the two photos on show, and 100 for an exact pair.

### 5.5 Keeper and marks

- The suggested keeper follows the setting: highest pixel count, oldest capture date, or newest capture date. Ties fall through pixel count, file size (larger), capture date (older), then path (shorter, then alphabetical), so the choice is always the same for the same files.
- Each member carries a mark: suggested keep, suggested recycle, keep or recycle. A group is decided when no mark is a suggestion. The engine refuses any change that would leave a group with no keeper.

### 5.6 Index

One SQLite database, `%LOCALAPPDATA%\DoubleTake\index.db`, in WAL mode, with `PRAGMA user_version` as the schema version and forward-only migrations.

| Table | Holds |
| --- | --- |
| `files` | path, size, modified time, pixel size, format, capture date, camera, BLAKE3, pHash, dHash, embedding, read error, last scan seen |
| `scans` | start, end, folders, closeness, similar shots, counts, state |
| `groups` | scan, kind, likeness, bytes to recover, decided, order |
| `members` | group, file, mark |
| `undo_log` | scan, group, the marks before each of the last 100 decisions |
| `cleanups` | scan, time, photo count, bytes, state |
| `cleanup_files` | clean-up, original path, size, the kept file's path, restored |

A database that cannot be opened or migrated is reported, never silently replaced. Clearing the index removes scan data (`files`, `scans`, `groups`, `members`, `undo_log`) and keeps the clean-up tables, so History survives.

### 5.7 Recycle and restore

- Recycling takes the files marked recycle in decided groups. Before each file moves, its size and modified time are checked against the index; a file that changed or is gone is skipped and counted.
- Files move with `IFileOperation` and `FOFX_RECYCLEONDELETE`, with no shell prompts. A file on a volume with no Recycle Bin is skipped and counted, never deleted.
- Each clean-up is written to `cleanups` and `cleanup_files` as files move, so a crash loses no record.
- Restore finds each file in the Recycle Bin by its original path and deletion time through the Recycle Bin shell folder and invokes the shell's own restore. A clean-up's state is read back from the bin: all there, some there, none there.

### 5.8 Logging

A text log at `%LOCALAPPDATA%\DoubleTake\logs\doubletake.log`, rotated at 1 MB with five files kept. It records scans, unreadable files with the reason, recycle and restore results, and errors. It never records photo contents.

## 6. Application

- `appcore` holds one view model per page (`ScanViewModel`, `ScanningViewModel`, `ReviewViewModel`, `HistoryViewModel`, `SettingsViewModel`) and a `ShellViewModel` for navigation and notices. They talk to the engine and to small interfaces (`IFolderPicker`, `IShell`, `IHttp`, `IClock`, `IUiQueue`) that tests replace with fakes.
- `app` is XAML and thin code-behind. It builds its resource dictionary from `design/tokens.json` through a generated file, so no colour or size is typed twice.
- Settings are `%LOCALAPPDATA%\DoubleTake\settings.json`, written atomically. An unreadable file is renamed aside and defaults are used.
- Thumbnails in the queue and strip come from the Windows shell thumbnail cache (`IShellItemImageFactory`). The compare panes decode through the engine at pane size, with a 64 MB cache.
- One instance at a time: a second start brings the first window forward.
- The update check runs once at start when the setting allows, off the UI thread, with a 10 second limit. It reads `version.json` (`{"version": "0.2.0", "url": "https://..."}`), compares versions numerically, and accepts a `url` only when it is `https` and its host is on the built-in list (the project's GitHub and the project website). A failure is logged and shows nothing, except after `Check now`.
- Command line, for tests and support: `--data-dir <folder>` moves the index, settings and logs; `--no-update-check`; `--scan <folder>` (repeatable) fills the folder list.

## 7. Similar shots

- Runtime: ONNX Runtime with the DirectML provider and a CPU fallback, shipped in the installer.
- Model: DINOv2 ViT-S/14 in ONNX form (Apache-2.0), pinned by URL, size and SHA-256 in `resources/model.json`. The candidate source is the Hugging Face repository `onnx-community/dinov2-small`; the section that pins it must confirm the file exists and its licence before relying on it, and otherwise export the model itself and host it as a GitHub release asset.
- The model is downloaded to `%LOCALAPPDATA%\DoubleTake\models\` only after the user agrees, verified against its SHA-256, and deleted if the check fails.
- Embeddings are computed for photos no hash group claimed, stored in `files.embedding`, and compared by cosine similarity. Pairs above 0.90 form `Similar` groups, shown after the duplicate groups and never mixed with them. The limit is set by the fixture test.

## 8. Testing

- `tests/fixtures/make_fixtures.py` generates the photo set into `build/fixtures/` from drawn scenes: each scene as an original, a resize, two recompressions, a rotation stored through EXIF, a light edit and a crop, beside scenes that look alike but are different photos. A manifest labels every pair duplicate or different.
- HEIC and RAW cannot be generated by the script. A few small sample files are committed under `tests/fixtures/samples/` with their source and licence in a README beside them.
- Engine and `appcore` tests are Catch2 programs run by `scripts/check.ps1`. Every fix gets a test that fails without it.
- `doubletake-uitests` starts the app with `--data-dir` on a fixture set, drives it through UI Automation, and checks what the SPEC says is on screen. `scripts/capture.ps1` saves each state in SPEC section 14 to `build/renders/`.
- A test that starts a process stops its whole process tree on timeout and teardown, and passes `CREATE_NO_WINDOW` to console children.

## 9. Release

- `version.props` is the only place the version is written. The app, the installer and `version.json` read it.
- `installer/DoubleTake.iss` installs per user to `%LOCALAPPDATA%\Programs\DoubleTake`, adds a Start menu entry and an uninstaller, and leaves the user's index and settings in place on uninstall unless asked.
- A release workflow builds Release on a tag, compiles the installer, and attaches it and its SHA-256 to a draft GitHub release. Publishing the release is the owner's step.
- `NOTICE.md` lists every third-party component with its licence, generated from the vcpkg and NuGet manifests, and is installed with the app.

## 10. Phases

| Phase | Name | Ends when |
| --- | --- | --- |
| 0 | Repository and tooling | The empty solution builds, tests run, CI is green, brand files are generated |
| 1 | Engine | `doubletake-cli` scans the fixtures, groups them correctly, recycles and restores |
| 2 | Application shell | The window opens in the Darkroom frame with navigation, settings storage and notices |
| 3 | Screens | Every page and dialog in the SPEC works on real folders |
| 4 | Similar shots | The optional model downloads, runs and adds Similar groups |
| 5 | Release | The installer installs, runs and uninstalls, and the release workflow produces it |
| 99 | Manual, operator only | Steps only the owner can take |

## 11. For the owner

These do not block the build. Each is a row in `todo/99-manual/`.

- The project website's address, for the `Website` link and for `version.json`'s `url`. Until it exists both point at the GitHub repository.
- Code signing (D10).
- Uploading the social preview image in the GitHub repository settings.
- Publishing each release.
