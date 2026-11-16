---
schema_version: 1
id: application-shell
domain: 02-app
status: active
title: "TODO-01 -- Application shell"
depends_on: ["repo-and-build", "match-and-clean"]
---

# TODO-01 -- Application shell

> **Goal:** DoubleTake opens as a WinUI 3 window in the Darkroom frame: the custom title bar with its tabs, an empty page for each tab, the notice bar and dialog frame, settings that persist, one instance at a time, and a test program that can drive the window and capture it.

> **Current state:** Measured 2026-11-16. The engine is complete (`D01 T01`, `D01 T02`) and runs from `doubletake-cli`. `resources/brand/` holds the generated icon and `resources/fonts/` the Space Grotesk font (`D00 T01 §9`). There is no `src/appcore/`, no `src/app/` and no window.

## Inputs

- `design/SPEC.md` sections 2, 3, 9, 11 and 12, `design/tokens.json`, and `design/mockups/darkroom/Scan.dc.html` for the title bar's measurements.
- `docs/plans/2026-11-16-doubletake-foundation.md` sections 2 (D3, D13), 3, 6 and 8 (called "the foundation plan" below).
- `resources/brand/doubletake.ico` and `resources/fonts/` from `D00 T01 §9`.

## Outcome

- `build\bin\x64\Debug\DoubleTake.exe` opens a 1280 x 800 dark window with the title bar of `design/SPEC.md` section 3, and switching tabs shows an empty page for each.
- `doubletake-uitests` starts the app on its own data folder, finds the tabs by name, and saves a capture.

**Adjacency:** list=not-applicable (the shell lists nothing; pages own their lists); document=not-applicable (nothing is carried or printed); settings=applicable @ D02 T01 §2; reporting=not-applicable (no data is summarised here); notifications=applicable @ D02 T01 §8; permissions=not-applicable (the shell refuses nothing; pages own their refusals); audit=not-applicable (the engine log is the trail, D01 T01 §1); exchange=not-applicable (settings are private to the app); reverse=not-applicable (the shell creates no record)

**Adjacency rationale:** The settings store in §2 is what every later setting is kept in, and each setting's consumer is named where the setting is built. The notice bar and dialog frame in §8 are how every page tells the user something, so they are built once here.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | appcore library and its test program | D00 T01 §4, D01 T02 §10 | [ ] |
| 2 | §2 | Settings store | §1 | [ ] |
| 3 | §3 | Text, number and date formatting | §1 | [ ] |
| 4 | §4 | WinUI 3 app project that opens a window | §1, D00 T01 §9 | [ ] |
| 5 | §5 | Theme resources generated from the tokens | §4 | [ ] |
| 6 | §6 | Title bar, tabs and page frame | §5, §10 | [ ] |
| 7 | §7 | Window size, position and single instance | §6, §2 | [ ] |
| 8 | §8 | Notice bar and dialog frame | §6 | [ ] |
| 9 | §9 | Command-line switches and data folder | §4, §2 | [ ] |
| 10 | §10 | UI Automation test program and capture script | §9 | [ ] |
| 11 | §11 | Contrast theme and text scaling in the shell | §7, §8 | [ ] |

Sections run in dependency order, not number order: §9 and §10 come straight after §5, so the UI test program exists before the sections whose checkpoints use it (§6, §7, §8, §11).

## 1. appcore library and its test program

The home of every view model, with no XAML in it.

**Phase:** 2
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/doubletake-appcore.vcxproj`. Done when: it builds a static library.
2. Add `tests/appcore/doubletake-appcore-tests.vcxproj`. Done when: one test passes.

- [ ] Add `src/appcore/doubletake-appcore.vcxproj` (static library, linking the engine, no WinRT projection headers) with `include/doubletake/app/observable.h` holding `Observable` (subscribe, unsubscribe, notify by property id) (foundation plan D13, section 6). Done when: the library builds. Cheaper substitute: view models written in XAML code-behind, which cannot be tested without a window.
- [ ] Add the service interfaces `IFolderPicker`, `IShell` (open a file, show in folder, open a URL, open the Recycle Bin), `IHttp`, `IClock` and `IUiQueue` in `include/doubletake/app/services.h`, with fakes in `tests/appcore/fakes.h`. Done when: a test calls each fake. Cheaper substitute: calling Win32 directly from view models.
- [ ] Add `tests/appcore/doubletake-appcore-tests.vcxproj` (Catch2) to the solution, with `observable_tests.cpp` covering notify, unsubscribe during notify, and no call after unsubscribe. Done when: `scripts/check.ps1` runs it. Cheaper substitute: none needed.
- [ ] Commit: `appcore: library, services and test program`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[observable]"` passes, and fails when unsubscribe leaves the subscriber registered.

## 2. Settings store

One file, written safely, read back the same.

**Phase:** 2
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/settings.cpp`. Done when: settings round-trip.
2. Survive a bad file. Done when: defaults load and the bad file is kept aside.

- [ ] Add `dt::app::Settings` in `src/appcore/settings.cpp` with every value and default in `design/SPEC.md` section 8, plus the folder list, the closeness, the window placement and the dismissed update version, stored as JSON at `<data folder>\settings.json` (foundation plan section 6). Done when: `tests/appcore/settings_tests.cpp` writes every value, reloads and compares. Cheaper substitute: the registry, which a test cannot isolate.
- [ ] Write atomically: to a temporary file in the same folder, flushed, then `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`, which both creates the file on first run and replaces it afterwards. Done when: a test saves with no file present, saves again over it, and a third save failed midway (through a fault hook) leaves the second file intact. Cheaper substitute: `ReplaceFile`, which fails when there is no file yet, or truncating and rewriting in place.
- [ ] On an unreadable or wrongly typed file, rename it to `settings.bad-<timestamp>.json`, load defaults and report it once. Done when: a test with broken JSON finds the renamed file and default values. Cheaper substitute: overwriting the user's file silently.
- [ ] Ignore unknown keys and keep them on the next save. Done when: a test with an extra key finds it still there after a save. Cheaper substitute: dropping keys a newer version wrote.
- [ ] Notify through `Observable` when a value changes, and save within 500 ms of the last change. Done when: a test changing three values sees one write. Cheaper substitute: a write on every keystroke.
- [ ] Commit: `appcore: settings store`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[settings]"` passes, and fails when the write is not atomic.

## 3. Text, number and date formatting

Every string and every number shown, from one place.

**Phase:** 2
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `resources/strings/en-GB.json` and `src/appcore/text.cpp`. Done when: a string is fetched by id.
2. Add formatters. Done when: the SPEC's examples are tested.

- [ ] Add `resources/strings/en-GB.json` holding every interface string in `design/SPEC.md` sections 3 to 10 under stable ids, with `{name}` placeholders, and `dt::app::text(id, args)` in `src/appcore/text.cpp` (`design/SPEC.md` section 12). Done when: a test fetches a string with two placeholders. Cheaper substitute: literals in XAML and C++, which cannot be reviewed in one place.
- [ ] Add a build step, `scripts/gen-strings.py`, turning the JSON into `build/generated/strings.h` (an id enum and a table), and fail the build on a duplicate id or a missing placeholder. Done when: a duplicated id breaks the build with its name. Cheaper substitute: loading the JSON at run time, where a typo is found by a user.
- [ ] Add `format_size(bytes)`: one decimal below 10 units, none from 10, in MB or GB (`0.6 MB`, `3.8 GB`, `412 MB`), with the user's decimal separator. Done when: tests cover the SPEC's three examples, 0 bytes and 1 TB. Cheaper substitute: `StrFormatByteSize`, which gives other rounding.
- [ ] Add `format_count(n)`, `format_date(time)`, `format_time(time)` and `format_duration(seconds)` (`0:44`, `1:02:10`) using the user's Windows regional format. Done when: tests under two locales give the expected text. Cheaper substitute: a fixed English format.
- [ ] Add plural forms for the strings that count (`1 photo`, `2 photos`, `1 folder`, `3 folders`, `1 clean-up`). Done when: tests cover 0, 1 and 2 for each. Cheaper substitute: `1 photos`.
- [ ] Commit: `appcore: strings and formatting`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[text]"` passes, and fails when `format_size` shows a decimal at 412 MB.

## 4. WinUI 3 app project that opens a window

The first window.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 3, first two bullets.
**Job:** the user starts DoubleTake and gets its window.
**Treatment:** a dark, empty window at the default size with the app's icon. Cheaper substitute that fails: a light default window that flashes white before the theme loads.
**Chrome:** a WinUI 3 `Window` with `RequestedTheme` dark on its root and the `ground` colour as background.

**Build order:**

1. Add `src/app/DoubleTake.vcxproj`. Done when: it builds an unpackaged, self-contained WinUI 3 executable.
2. Open the window. Done when: it shows at 1280 x 800 with the icon.

- [ ] Add `src/app/DoubleTake.vcxproj` (C++/WinRT, Windows App SDK and C++/WinRT from NuGet with versions pinned in `packages.config`, `WindowsPackageType` `None`, `WindowsAppSDKSelfContained` `true`) with `App.xaml` and `MainWindow.xaml`, linking `appcore` (foundation plan D3). Done when: `scripts/build.ps1` builds `DoubleTake.exe` and it starts on a machine with no Windows App SDK runtime installed (checked by running it with the runtime's package absent from `Get-AppxPackage`, or by listing the SDK's files beside the executable). Cheaper substitute: a packaged app, which needs MSIX and a certificate.
- [ ] Add `scripts/smoke-launch.ps1 [-AppArgs <args>]`: start the built app with no console window, wait up to 15 seconds for its top-level window, read the colour of the client area's centre pixel with `PrintWindow`, close the window, and end the whole process tree on timeout or failure. Done when: it exits 0 printing the window's size and that pixel, and exits 1 when the app shows no window. Cheaper substitute: checking only that the process started, which passes for an app that never shows.
- [ ] Set the window to 1280 x 800 effective pixels, centred on the monitor under the pointer, with background `ground` and the dark theme set before first paint. Done when: `scripts/smoke-launch.ps1` reports 1280 x 800 at 100% scale and the centre pixel `#141312`. Cheaper substitute: setting the theme after `Activate`, which flashes.
- [ ] Set the window and taskbar icon from `resources/brand/doubletake.ico` and embed it as the executable's icon with a version resource reading `$(DoubleTakeVersion)`. Done when: Explorer shows the icon and the file's properties show the version. Cheaper substitute: the default WinUI icon.
- [ ] Add an application manifest declaring per-monitor DPI awareness (v2), long path awareness and Windows 10 and 11 compatibility. Done when: `mt.exe -inputresource` shows the three entries. Cheaper substitute: a blurry window on a second monitor.
- [ ] Route unhandled errors to the engine log and a plain message box naming the log folder, then exit. Done when: a test build's forced error writes the log line and shows the box. Cheaper substitute: a silent crash.
- [ ] Commit: `app: WinUI 3 project and first window`

**Test checkpoint:** `pwsh scripts/build.ps1` builds `build\bin\x64\Debug\DoubleTake.exe` and `pwsh scripts/smoke-launch.ps1` exits 0 with the centre pixel `#141312`, and exits 1 when `MainWindow` is never activated.

## 5. Theme resources generated from the tokens

Colours, type and sizes come from `design/tokens.json`, typed once.

**Phase:** 2
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `scripts/gen-theme.py`. Done when: it writes a XAML resource dictionary.
2. Load it. Done when: a page uses a token by name.

- [ ] Add `scripts/gen-theme.py` turning `design/tokens.json` into `build/generated/Theme.xaml`: a `SolidColorBrush` and `Color` per colour (`DtGround`, `DtAccent`), a `x:Double` per size and radius, and a `Style` per type style in `design/SPEC.md` section 2. Done when: the file holds an entry for every token. Cheaper substitute: hex values typed into each page.
- [ ] Run it as a pre-build step of the app project and merge the result into `App.xaml`. Done when: changing `accent` in the tokens and rebuilding changes the running app. Cheaper substitute: a generated file committed and forgotten.
- [ ] Load Space Grotesk from `resources/fonts/` as an app font, with `Segoe UI Variable Text` as the interface font. Done when: a capture of a `pageTitle` text block shows Space Grotesk's glyphs (the double-storey `g` differs from Segoe's). Cheaper substitute: relying on the font being installed.
- [ ] Override the WinUI theme resources the controls read (`AccentFillColorDefaultBrush` and its pointer-over and pressed forms, `TextOnAccentFillColorPrimaryBrush`, the control corner radius, focus visual colours) with token values. Done when: a default `Button` with the accent style is amber with dark text. Cheaper substitute: restyling every control by hand.
- [ ] Add `scripts/tests/test_gen_theme.py` checking every token appears once and that a colour not six hex digits is refused. Done when: `python -m unittest scripts.tests.test_gen_theme` passes. Cheaper substitute: none needed.
- [ ] Commit: `app: theme resources generated from the tokens`

**Test checkpoint:** `python -m unittest scripts.tests.test_gen_theme` passes, and fails when a token is left out of the generated dictionary.

## 6. Title bar, tabs and page frame

The frame every page lives in.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 3, and the title bar markup of `design/mockups/darkroom/Scan.dc.html`.
**Job:** the user sees where they are and moves between Scan, Review, History and Settings.
**Treatment:** a 48 high app-drawn title bar holding the icon, the wordmark, three tabs and the Settings button, with the system caption buttons. Cheaper substitute that fails: a `NavigationView` side pane, which is another design.
**Chrome:** `ExtendsContentIntoTitleBar`, a custom drag region, tabs as `RadioButton`s restyled to text with an accent underline, and a `Frame` for pages.

**Build order:**

1. Add `ShellViewModel` and the title bar XAML. Done when: the bar matches the mockup's measurements.
2. Add navigation. Done when: each tab shows its page.

- [ ] Add `dt::app::ShellViewModel` in `src/appcore/shell.cpp` with the current page (`Scan`, `Scanning`, `Review`, `History`, `Settings`), `navigate(page)`, and `review_enabled`, false until a scan with at least one group exists. Done when: `tests/appcore/shell_tests.cpp` covers navigation, the disabled Review tab, and Scan showing `Scanning` while a scan runs. Cheaper substitute: navigation state held in the XAML frame.
- [ ] Build the title bar in `src/app/MainWindow.xaml`: height 48, a 1 px `raised` line under it, the icon at 22 with 14 left padding, the wordmark `doubletake` in the `wordmark` style, 20 before the tabs. Done when: UI Automation reports the bar's height as 48 and a capture matches the mockup's left edge within 1 px. Cheaper substitute: the system title bar with tabs below it, which adds 32 px of height.
- [ ] Add the three tabs with the current tab in `bodyStrong` and `text` with a 2 px `accent` line inset 14 each side, others in `body` and `textMuted`, and Review disabled per the view model. Done when: a UI test selects each tab and reads the selected state, and finds Review disabled on first run. Cheaper substitute: a `TabView`, whose chrome and close buttons are not in the design.
- [ ] Add the Settings button (36 x 32, sliders glyph, named `Settings`) with the `raised` fill and `accent` glyph while Settings shows, and no tab selected then. Done when: a UI test opens Settings and finds no tab selected. Cheaper substitute: a fourth tab.
- [ ] Set the drag region to the bar minus its interactive elements and keep the system caption buttons, tall. Done when: dragging the empty part moves the window and double-clicking it maximises. Cheaper substitute: a whole-bar drag region that swallows clicks on the tabs.
- [ ] Host pages in a `Frame` under the bar with an empty `Page` per destination, and no transition animation. Done when: a UI test finds a different page automation id after each tab. Cheaper substitute: showing and hiding panels in one page.
- [ ] Commit: `app: title bar, tabs and page frame`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[shell]"` passes, and fails when the Review tab is enabled with no scan.

## 7. Window size, position and single instance

The window comes back where it was, and there is only ever one.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 3, first bullet, and foundation plan section 6 ("One instance at a time").
**Job:** the user reopens the app and finds the window where they left it.
**Treatment:** placement saved on close and restored on open, clamped to the screens that exist now. Cheaper substitute that fails: restoring to a monitor that is no longer connected, leaving the window off screen.
**Chrome:** none of its own; this section changes placement only.

**Build order:**

1. Save and restore placement. Done when: it survives a restart.
2. Enforce one instance. Done when: a second start focuses the first.

- [ ] Enforce the minimum size 1024 x 680 effective pixels at any DPI. Done when: a UI test resizing to 600 x 400 reads back 1024 x 680. Cheaper substitute: a layout that breaks below the minimum.
- [ ] Save size, position and maximised state to the settings on close, and restore them on open. Done when: a UI test moves and resizes the window, restarts the app and reads the same rectangle. Cheaper substitute: always opening at the default.
- [ ] Clamp a restored rectangle to the visible work areas, falling back to the default size centred when less than 100 px of it is visible. Done when: a test of the clamp function with a rectangle on a missing monitor returns a visible one. Cheaper substitute: none needed.
- [ ] Hold a named mutex scoped to the data folder; a second start with the same data folder activates the first window and exits 0. Done when: a UI test starting a second process finds one window and the second process gone. Cheaper substitute: two instances writing one index.
- [ ] Commit: `app: window placement and single instance`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[window]"` passes, and fails when placement is not saved on close.

## 8. Notice bar and dialog frame

How the app tells the user something, built once.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 9, opening paragraph, and `design/mockups/darkroom/Dialogs.dc.html`.
**Job:** the user reads a result, a problem or a question and answers it.
**Treatment:** a 48 high `raised` bar at the top of the page for notices; a 480 wide dialog over a scrim for questions. Cheaper substitute that fails: a system message box, which leaves the design and cannot hold progress.
**Chrome:** an `InfoBar`-like custom control and a restyled `ContentDialog`.

**Build order:**

1. Add notices to `ShellViewModel` and the bar. Done when: a notice shows and dismisses.
2. Add the dialog frame. Done when: it matches the mockup.

- [ ] Add `dt::app::Notice` (kind `Info`, `Result`, `Problem`, `Update`; message; optional action label and callback; dismissible) and a notice queue on `ShellViewModel` showing one at a time, newest replacing an `Info`. Done when: `tests/appcore/shell_tests.cpp` covers show, replace, action and dismiss. Cheaper substitute: notices raised straight from XAML.
- [ ] Build `src/app/Controls/NoticeBar.xaml`: 48 high, `raised`, a glyph (`accent` arrow for `Update`, a warning glyph for `Problem`, a tick for `Result`), the message with its first sentence in `bodyStrong`, the action as an accent button 32 high, and a 32 x 32 dismiss button named `Dismiss`. Done when: a UI test raises each kind through a test hook and reads the text and the button names. Cheaper substitute: the stock `InfoBar` colours, which are not in the tokens.
- [ ] Mark the bar as a live region so its text is announced. Done when: UI Automation reports `LiveSetting` polite on the bar. Cheaper substitute: a notice only sighted users notice.
- [ ] Restyle `ContentDialog` as `DtDialog` in `src/app/Controls/DtDialog.xaml`: 480 wide, `panel` body with 24 padding, `stroke` border, radius 10, the `dialogTitle` style, a `ground` footer with two equal 36 high buttons, the action on the left in accent, over the `scrim` at 70%. Done when: a capture of a test dialog matches the mockup's dialog within 2 px on each edge. Cheaper substitute: the stock dialog, whose buttons are the other way round.
- [ ] Close the dialog on Escape as cancel, and return focus to the control that opened it. Done when: a UI test confirms both. Cheaper substitute: focus lost to the window.
- [ ] Show a `Problem` notice with the action `Start a new index` when the index cannot be opened at start (`D02 T01 §9` reports the failure), and keep the Scan page usable (`design/SPEC.md` section 10, last row); the action itself is built by `D03 T03 §6` and until then opens the data folder. Done when: a UI test with a corrupt `index.db` finds the notice and an enabled Scan tab. Cheaper substitute: refusing to start.
- [ ] Commit: `app: notice bar and dialog frame`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[notice]"` and `-Filter "[dialog]"` pass, and fail when the dialog's action button is on the right.

## 9. Command-line switches and data folder

What tests and support need to run the app in isolation.

**Phase:** 2
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/startup.cpp`. Done when: switches parse.
2. Use the data folder everywhere. Done when: nothing is written outside it.

- [ ] Add `dt::app::StartupOptions` parsed in `src/appcore/startup.cpp`: `--data-dir <folder>`, `--no-update-check`, `--scan <folder>` (repeatable) (foundation plan section 6). Done when: `tests/appcore/startup_tests.cpp` covers each, quoted paths, and an unknown switch reported as an error. Cheaper substitute: environment variables, which leak between tests.
- [ ] Resolve the data folder to `%LOCALAPPDATA%\DoubleTake` by default and create it; open the index, settings and log only under it. Done when: `scripts/smoke-launch.ps1 -AppArgs "--data-dir build\smoke-data"` leaves a `settings.json` there and the default folder's file list unchanged. Cheaper substitute: a path built in three places.
- [ ] On an unknown switch show a plain message naming it and exit 2 without opening the window. Done when: a test starts the app with `--bogus` and reads exit code 2. Cheaper substitute: ignoring it.
- [ ] Open the index at start and hand a failure to `ShellViewModel` as a startup problem value, without ending the app. Done when: `tests/appcore/startup_tests.cpp` opens a corrupt file through the startup path and reads the problem value. Cheaper substitute: an unhandled error at start.
- [ ] Commit: `app: command-line switches and data folder`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[startup]"` passes, and fails when `--data-dir` is ignored.

## 10. UI Automation test program and capture script

The way every screen after this is proven.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** no

**Build order:**

1. Add `tests/ui/doubletake-uitests.vcxproj`. Done when: it starts the app and finds a tab.
2. Add `scripts/capture.ps1`. Done when: a PNG of the window is saved.

- [ ] Add `tests/ui/doubletake-uitests.vcxproj` (Catch2, the UI Automation COM client) with `tests/ui/app_fixture.h`: start `DoubleTake.exe` with a fresh `--data-dir` under `build/ui-test/` and `--no-update-check`, wait up to 15 seconds for the window, and expose find-by-name, find-by-automation-id, invoke, set-value and send-keys helpers (foundation plan section 8). Done when: `[launch]` finds the app's window by its automation id and reads its title. Cheaper substitute: tests that poke view models and never see the real window.
- [ ] Capture the first painted frame in `[launch]` and fail on any pure white pixel. Done when: the test passes, and fails when the dark theme is applied after the window is shown. Cheaper substitute: checking the colour a second later, which misses a white flash.
- [ ] End the app on teardown: close the window, wait 5 seconds, then end the whole process tree with a job object. Done when: after a test that leaves a dialog open, no `DoubleTake.exe` is left. Cheaper substitute: `TerminateProcess` on the one handle, which can leave children.
- [ ] Add a test hook, active only with `--test-hooks`, exposing named commands to the fixture over a local named pipe (raise a notice, open a dialog, set a fake clock). Done when: a `[hook]` test sends the `ping` command and reads its reply, and the pipe does not exist without the switch. Cheaper substitute: test-only buttons in the shipped interface.
- [ ] Add `scripts/capture.ps1 -Name <state>` saving the app window's client area to `build/renders/<state>.png` with `PrintWindow`, and a fixture helper that calls it. Done when: `[launch]` leaves `build/renders/shell-first-run.png`, non-empty and 1280 x 800 at 100% scale. Cheaper substitute: a full-screen screenshot that includes the desktop.
- [ ] Add the UI test program to `scripts/check.ps1` under the name `ui`, skipped with a clear line when there is no interactive desktop. Done when: `-Only ui` runs it. Cheaper substitute: a silent skip that reads as a pass.
- [ ] Commit: `tests: UI Automation test program and capture script`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[launch]"` passes and writes `build/renders/shell-first-run.png`, and fails when the app is started with a switch that prevents the window.

## 11. Contrast theme and text scaling in the shell

The frame holds under the accessibility settings of `design/SPEC.md` sections 3 and 11.

**Phase:** 2
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 3, second bullet, and section 11, first and last bullets.
**Job:** a user with a contrast theme or large text can use the frame.
**Treatment:** system colours under a contrast theme, a 2 px focus outline on every control, and a layout that holds at 200% text. Cheaper substitute that fails: custom dark colours forced over the user's contrast theme.
**Chrome:** `HighContrast` theme dictionaries beside the generated dark one.

**Build order:**

1. Add the contrast dictionary. Done when: the frame uses system colours.
2. Check scaling and focus. Done when: captures are saved for each.

- [ ] Add a `HighContrast` theme dictionary mapping every token brush to a system colour resource (`ground` to window, `text` to window text, `accent` to highlight, `onAccent` to highlight text, strokes to window text). Done when: with a contrast theme on, a capture's title bar background equals the system window colour. Cheaper substitute: ignoring the user's theme.
- [ ] Give every focusable control in the shell a 2 px `accent` focus outline with 2 px offset. Done when: a UI test tabbing through the bar finds each control focused in order: tabs, Settings, then the page. Cheaper substitute: the default 1 px outline, which is hard to see on dark.
- [ ] Verify the bar at 200% text scaling and at the minimum window size: no clipped tab text and no overlap with the caption buttons. Done when: `build/renders/shell-text-200.png` and `shell-min-size.png` are saved and a UI test finds every tab's bounding box inside the window. Cheaper substitute: fixed pixel font sizes that ignore the setting.
- [ ] Add `Ctrl+1`, `Ctrl+2`, `Ctrl+3` and `Ctrl+,` as keyboard accelerators on the window. Done when: a UI test sends each and reads the current page. Cheaper substitute: accelerators on one page only.
- [ ] Commit: `app: contrast theme, focus and text scaling in the shell`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[shell-a11y]"` passes, and fails when a tab loses its automation name.

## Verification

- `DoubleTake.exe` opens in the Darkroom frame, moves between four empty pages by pointer and keyboard, remembers its placement, and refuses a second instance; `doubletake-uitests` proves each and saves captures to `build/renders/`.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
