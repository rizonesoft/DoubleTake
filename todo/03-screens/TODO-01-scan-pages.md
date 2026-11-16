---
schema_version: 1
id: scan-pages
domain: 03-screens
status: active
title: "TODO-01 -- Scan and Scanning pages"
depends_on: ["application-shell"]
---

# TODO-01 -- Scan and Scanning pages

> **Goal:** The Scan page and the Scanning page of `design/SPEC.md` sections 4 and 5 work on real folders: adding folders by drop or picker, the list rules, the closeness choice, starting a scan, live progress, cancel, and the hand-over to Review.

> **Current state:** Measured 2026-11-16. `D02 T01` gives the window frame with an empty page per tab, `ShellViewModel`, the settings store, strings, the notice bar and the UI test program. The engine's `dt::scan` and matching are complete (`D01 T01 §9`, `D01 T02 §5`). No page has content.

## Inputs

- `design/SPEC.md` sections 4, 5, 10 (first row), 11 and 12.
- `design/mockups/darkroom/Scan.dc.html` and `Scanning.dc.html`.
- `docs/plans/2026-11-16-doubletake-foundation.md` sections 5.1 and 6 (called "the foundation plan" below).
- -> XREF: D04 T01 §5 -- the Similar shots switch built in §3 opens the model dialog owned there

## Outcome

- Dropping three folders, choosing `Close` and pressing `Start scan` shows live progress and ends on the Review tab with groups in the index.
- Every state of Scan and Scanning in `design/SPEC.md` section 14 has a capture in `build/renders/`.

**Adjacency:** list=applicable @ D03 T01 §2; document=not-applicable (nothing is carried or printed); settings=applicable @ D03 T01 §3; reporting=applicable @ D03 T01 §6; notifications=applicable @ D03 T01 §1; permissions=applicable @ D03 T01 §1; audit=not-applicable (the engine log records each scan, D01 T01 §1); exchange=not-applicable (SPEC section 15 rules out import and export); reverse=applicable @ D03 T01 §4

**Adjacency rationale:** The folder chips are the list. The closeness and Similar shots controls are settings consumed by the scan in §4. The status bar reports the last scan. The folder rules raise notices and refuse nested or unreachable folders. Cancel is the reverse of starting a scan, and removing a chip the reverse of adding a folder.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Scan view model: folder list rules | D02 T01 §10, D02 T01 §11 | [ ] |
| 2 | §2 | Scan page: drop zone and folder chips | §1 | [ ] |
| 3 | §3 | Scan page: matching panel and Start scan | §2 | [ ] |
| 4 | §4 | Scanning view model | §1, D01 T02 §5 | [ ] |
| 5 | §5 | Scanning page | §4, §3 | [ ] |
| 6 | §6 | Status bar and the end of a scan | §5 | [ ] |

## 1. Scan view model: folder list rules

The state behind the Scan page, tested with fakes and no window.

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/scan_vm.cpp`. Done when: the folder list follows the rules.
2. Count photos in the background. Done when: counts arrive without blocking.

- [ ] Add `dt::app::ScanViewModel` in `src/appcore/scan_vm.cpp` with `folders` (path, count state `Counting`, `Counted(n)` or `NotFound`), loaded from and saved to the settings (`design/SPEC.md` section 4, item 4). Done when: `tests/appcore/scan_vm_tests.cpp` reloads a saved list. Cheaper substitute: a list forgotten on close.
- [ ] Add `add_folders(paths)` applying the rules in order: skip a path already listed (compared without case and without a trailing separator); skip a path inside a listed folder and raise the notice `Already inside <parent>`; when a path is a parent of listed folders, remove them and add it. Done when: tests cover each rule, a mixed batch, and `C:\Photos` beside `C:\Photos2`, which are not nested. Cheaper substitute: a prefix string compare, which calls `C:\Photos2` a child of `C:\Photos`.
- [ ] Ignore paths that are files, and paths that do not exist at add time, raising a `Problem` notice for the latter. Done when: tests cover both. Cheaper substitute: adding a file's parent folder without being asked.
- [ ] Add `remove_folder(path)`. Done when: a test removes one and the settings no longer hold it. Cheaper substitute: none needed.
- [ ] Count each folder's photos on a background task using `dt::walk` with the current scan options, cancellable, publishing through `IUiQueue`; mark a folder that cannot be opened `NotFound`. Done when: tests with the fake queue see `Counting` then `Counted`, and `NotFound` for a missing drive. Cheaper substitute: counting on the UI thread, which freezes the window on a large library.
- [ ] Expose `total_text` (`48,912 photos in 3 folders`, or `Add a folder to start` with no reachable folder) and `can_start`. Done when: tests cover zero folders, only unreachable folders, and counts still running (the text shows the count so far). Cheaper substitute: enabling Start with nothing to scan.
- [ ] Commit: `appcore: scan view model and folder rules`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[scan-vm]"` passes, and fails when the nested-folder rule uses a plain prefix compare.

## 2. Scan page: drop zone and folder chips

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 4, items 1 to 4, and `design/mockups/darkroom/Scan.dc.html`.
**Job:** the user tells DoubleTake which folders to look in.
**Treatment:** a large drop zone with a Browse button, and one chip per folder with its photo count and a remove button. Cheaper substitute that fails: a text box for typing paths.
**Chrome:** a custom drop target on `panel` with a dashed border, chips in a wrapping panel, standard buttons.

**Build order:**

1. Add `src/app/Pages/ScanPage.xaml`. Done when: the column, title and drop zone match the mockup.
2. Add the chips. Done when: they follow the view model.

- [ ] Add `src/app/Pages/ScanPage.xaml`: a 760 wide column centred, 48 below the title bar, 24 between blocks, with the title `Where are your photos?` in `pageTitle`. Done when: UI Automation reports the column 760 wide at 1280 and a capture matches the mockup's title position within 2 px. Cheaper substitute: a column that stretches with the window.
- [ ] Build the drop zone: 760 x 168, `panel` fill, a 1.5 px dashed `strokeStrong` border with radius 10, the folder glyph in `accent`, `Drop folders here` at 16, and the `Browse` button. Done when: a capture matches the mockup's zone within 2 px. Cheaper substitute: a solid border, since XAML borders have no dash; draw it with a `Rectangle` and `StrokeDashArray`.
- [ ] Accept dragged folders: while a drag carrying storage items is over the zone, show the solid `accent` border and `Drop to add`; on drop pass the folder paths to `add_folders` and ignore files. Done when: a UI test simulating the drop through the test hook adds a chip, and a file drop adds none. Cheaper substitute: accepting the drop anywhere in the window with no visible target.
- [ ] Wire `Browse` to `IFolderPicker`, implemented with `IFileOpenDialog` and `FOS_PICKFOLDERS | FOS_ALLOWMULTISELECT` owned by the window. Done when: a UI test with the picker replaced through the test hook adds two folders. Cheaper substitute: the WinRT `FolderPicker`, which picks one folder at a time.
- [ ] Add the chips: 36 high on `raised`, radius 6, the path, the count in `caption` `textMuted` (`counting`, a number, or `Not found`), and a 28 x 28 remove button named `Remove folder`, wrapping with 8 between. Done when: a UI test with three folders finds three chips, their counts, and removes the second. Cheaper substitute: a `ListView`, whose row chrome is not in the design.
- [ ] Ellipsise a long path in the middle so the drive and the last folder stay visible, with the full path as the chip's tooltip and automation name. Done when: a UI test with a 200 character path reads the full path from the automation name. Cheaper substitute: a chip wider than the column.
- [ ] Capture `scan-first-run`, `scan-three-folders`, `scan-drag-over` and `scan-folder-not-found` (`design/SPEC.md` section 14). Done when: the four PNGs exist and each differs from the others. Cheaper substitute: capturing only the mockup's state.
- [ ] Commit: `app: scan page drop zone and folder chips`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[scan-folders]"` passes, and fails when a dropped file adds a chip.

## 3. Scan page: matching panel and Start scan

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 4, items 5 to 7.
**Job:** the user chooses how close a match must be and starts the scan.
**Treatment:** a three-way choice with a caption that explains the current choice, a switch for Similar shots, and one large amber button. Cheaper substitute that fails: a numeric threshold the user has to guess.
**Chrome:** a custom segmented control on a `ground` track, a `ToggleSwitch` restyled to 40 x 20 with no On and Off text, and an accent button 44 high.

**Build order:**

1. Add the panel. Done when: both rows match the mockup.
2. Add Start and the total. Done when: Start begins a scan.

- [ ] Build the matching panel (`panel`, radius 10, two rows divided by a 1 px `raised` line, 16 x 20 padding) with `How close must a match be?` and the segmented control `Exact`, `Close`, `Loose`: track `ground` with radius 8 and 3 padding, segments 30 high with radius 6, the chosen one `accent` with `onAccent` text in weight 600. Done when: a capture matches the mockup within 2 px. Cheaper substitute: three radio buttons with default chrome.
- [ ] Bind the choice to the closeness setting and change the caption to the wording for each choice in `design/SPEC.md` section 4, item 5. Done when: a UI test selects each segment, reads its caption, restarts the app and finds the choice kept. Cheaper substitute: one caption for all three.
- [ ] Make the segmented control a single tab stop moved within by the left and right arrow keys, exposed to UI Automation as a radio group. Done when: a UI test focuses it and changes the choice with the arrow keys. Cheaper substitute: three tab stops with no group semantics.
- [ ] Add the `Similar shots` row with its caption and switch bound to the setting. Turning it on when no model is installed asks `ShellViewModel` for the model dialog. Until `D04 T01 §5` ships that dialog, the request raises the notice `Similar shots arrive in a later version.` and the switch returns to off. Done when: a UI test turns the switch on and finds it off again with the notice. Cheaper substitute: a switch that stays on and does nothing. -> XREF: D04 T01 §5
- [ ] Add `Start scan` (44 high, radius 8, `accent`, 16 px weight 700) with `total_text` beside it in `textMuted`, disabled when `can_start` is false, and started by `F5` too. Done when: a UI test finds it disabled with no folders and enabled with one. Cheaper substitute: an enabled button that shows an error after the click.
- [ ] Capture `scan-closeness-exact`, `scan-closeness-close` and `scan-closeness-loose`. Done when: the three PNGs exist. The `scan-similar-on` state is captured by `D04 T01 §5`, where the switch can stay on. Cheaper substitute: none needed.
- [ ] Commit: `app: scan page matching panel and start`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[scan-matching]"` passes, and fails when the closeness choice is not saved.

## 4. Scanning view model

The run of a scan: progress, cancel, the end.

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/scanning_vm.cpp`. Done when: it runs the engine off the UI thread.
2. Add the derived numbers. Done when: speed and time are tested with a fake clock.

- [ ] Add `dt::app::ScanningViewModel` in `src/appcore/scanning_vm.cpp`: `start(options)` runs `dt::scan_and_group` (`D01 T02 §5`), the one owner of the read, match and save sequence, on a background thread, publishing its progress through `IUiQueue`; the shell shows `Scanning` meanwhile. Done when: `tests/appcore/scanning_vm_tests.cpp` runs a scan of a small fixture folder to the end with the fake queue. Cheaper substitute: scanning on the UI thread.
- [ ] Expose the phase title (`Looking at your photos`, then `Comparing`), the current folder, `read_text` and `total_text`, the fraction, and `indeterminate` during `Comparing` with the line `<n> photos read` (`design/SPEC.md` section 5, items 1 and 2). Done when: tests check each in both phases. Cheaper substitute: a bar stuck at 100% while groups are formed.
- [ ] Expose `groups_so_far` (matching run on what is read so far, at most once every 2 seconds, off the UI thread), `photos_per_second` (over the last 5 seconds, with `IClock`) and `elapsed_text`. Done when: tests with the fake clock check the three. Cheaper substitute: a speed averaged over the whole scan, which hides a stall.
- [ ] Add `cancel()`: cancel the token, wait for the engine to return, and report `Scan cancelled. <n> photos read.` to the shell, which returns to Scan. Done when: a test cancels and finds the index holding the rows read so far and no `scans` row marked finished. Cheaper substitute: abandoning the thread.
- [ ] Refuse `start` while a scan runs, and refuse it with a `Problem` notice when no folder is reachable. Done when: tests cover both. Cheaper substitute: two scans writing one index.
- [ ] Expose the status line: `Reading <n> folders. <n> photos unchanged since the last scan were skipped.` and, with unreadable files, `<n> files could not be read.` with an `Open log` action through `IShell`. Done when: tests cover with and without unreadable files. Cheaper substitute: hiding read failures.
- [ ] Commit: `appcore: scanning view model`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[scanning-vm]"` passes, and fails when `cancel` does not wait for the engine.

## 5. Scanning page

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 5 and `design/mockups/darkroom/Scanning.dc.html`.
**Job:** the user sees the scan is working, how far it is, and can stop it.
**Treatment:** one large count, a thin progress bar, three stat cards and a Cancel button. Cheaper substitute that fails: a spinner with no numbers, which gives no way to judge a long scan.
**Chrome:** a `ProgressBar` restyled to 6 high with a `raised` track, three `panel` cards, a secondary button.

**Build order:**

1. Add `src/app/Pages/ScanningPage.xaml`. Done when: it matches the mockup.
2. Bind it. Done when: it moves during a real scan.

- [ ] Add `src/app/Pages/ScanningPage.xaml`: the 760 column 72 below the title bar with 28 between blocks, the title in `pageTitle`, and the current folder on one line, ellipsised at the start so the deepest folder stays visible. Done when: a capture matches the mockup within 2 px. Cheaper substitute: a wrapping path that makes the page jump.
- [ ] Add the count in `bigNumber` with `of <total> photos` at 16 in `textMuted` on the same baseline, in tabular figures so digits do not shift. Done when: a UI test reads both texts during a scan. Cheaper substitute: proportional digits, which make the number wobble as it counts.
- [ ] Add the progress bar: 6 high, radius 3, `raised` track, `accent` fill, determinate while reading and indeterminate while comparing, with its automation value set. Done when: a UI test reads a range value between 0 and 100 mid-scan. Cheaper substitute: the default bar height and colours.
- [ ] Add the three stat cards in a three-column grid, 12 apart: label in `caption` `textMuted`, value in `stat`, the groups value in `accent`. Done when: a UI test reads three labels and three values. Cheaper substitute: one line of text holding all three.
- [ ] Add `Cancel scan` (36 high, secondary) with its note, bound to `cancel()`, and `Esc` doing the same. Done when: a UI test cancels a scan of a large generated folder and lands on Scan within 2 seconds. Cheaper substitute: a confirm dialog the SPEC does not ask for.
- [ ] Update the page at most ten times a second and keep the window responsive. Done when: a UI test drags the window during a scan and the scan's elapsed time is not paused. Cheaper substitute: per-file updates that starve input.
- [ ] Capture `scanning-reading`, `scanning-comparing` and `scanning-unreadable` using the test hook to hold each state. Done when: the three PNGs exist. Cheaper substitute: none needed.
- [ ] Commit: `app: scanning page`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[scanning]"` passes, and fails when Cancel leaves the Scanning page showing.

## 6. Status bar and the end of a scan

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 4, item 7, and section 5, items 4 to 6.
**Job:** the user learns what the last scan found and is taken to the result.
**Treatment:** a 36 high bar along the bottom of Scan and Scanning with one line of text, and an automatic move to Review when a scan ends. Cheaper substitute that fails: leaving the user on a finished progress page.
**Chrome:** a bottom bar with a 1 px `raised` top line and `caption` text in `textMuted`.

**Build order:**

1. Add the status bar. Done when: each text shows in its state.
2. Hand over to Review. Done when: the tab opens after a scan.

- [ ] Add the status bar to both pages: 36 high, 16 side padding, text from the view models: `No scan yet`, `Last scan <date>: <n> groups, <size> to recover`, `Scan cancelled. <n> photos read.`, or the Scanning line. Done when: a UI test reads each of the four. Cheaper substitute: a status only in the log.
- [ ] Render the `Open log` action as a link in the bar that opens the log folder through `IShell`. Done when: a UI test invokes it and the fake shell records the folder. Cheaper substitute: a path the user has to copy.
- [ ] When a scan ends with groups, enable the Review tab and navigate to it. Done when: a UI test scanning the fixtures lands on Review with the tab enabled. Cheaper substitute: making the user click.
- [ ] When a scan ends with no groups, navigate to Review, which shows its `No duplicates found` state (owned by `D03 T02 §10`); until that section ships, Review shows an empty page. Done when: a UI test scanning a folder with no copies lands on Review. Cheaper substitute: staying on Scan with no word of the result. -> XREF: D03 T02 §10
- [ ] Announce the end of a scan through the notice bar's live region: `Scan finished. <n> groups found.` Done when: a UI test reads the notice. Cheaper substitute: a silent change of page.
- [ ] Commit: `app: scan status bar and hand-over to review`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[scan-end]"` passes, and fails when a finished scan leaves the Scan tab current.

## Verification

- On the build machine, dropping `build\fixtures` on the window, choosing each closeness in turn and pressing `Start scan` shows moving progress and ends on Review; cancelling midway returns to Scan with the cancelled text.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
