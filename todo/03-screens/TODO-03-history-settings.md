---
schema_version: 1
id: history-settings
domain: 03-screens
status: active
title: "TODO-03 -- History, Settings and the update notice"
depends_on: ["application-shell", "review-page"]
---

# TODO-03 -- History, Settings and the update notice

> **Goal:** The History page, the Settings page with About, and the update notice of `design/SPEC.md` sections 7, 8, 9.4 and 9.5 work end to end, every shortcut and automation name in section 11 is in place, and every state in section 14 has a capture.

> **Current state:** Measured 2026-11-16. Scan, Scanning and Review are complete (`D03 T01`, `D03 T02`). The engine lists clean-ups, reads their state from the Recycle Bin and restores them (`D01 T02 §8`, `§9`). The settings store holds every value (`D02 T01 §2`) but no page edits them. History and Settings are empty pages. Nothing checks for a new version.

## Inputs

- `design/SPEC.md` sections 7, 8, 9.4, 9.5, 9.6, 10, 11, 12 and 14.
- `design/mockups/darkroom/History.dc.html`, `Settings.dc.html` and `Dialogs.dc.html`.
- `docs/plans/2026-11-16-doubletake-foundation.md` sections 2 (D7, D12), 5.7 and 6 (called "the foundation plan" below).
- -> XREF: D03 T02 §9 -- the result notice's Undo calls the restore command of §3
- -> XREF: D04 T01 §5 -- the Similar shots row of §5 shows the model state and opens the dialog owned there
- -> XREF: D05 T01 §5 -- the release workflow publishes the `version.json` that §8 reads
- -> XREF: D99 T01 §1 -- the website address fills the Website link of §7 and the allowed hosts of §8

## Outcome

- History lists each clean-up with its true state, and `Restore` puts its photos back.
- Changing any setting takes effect at once and survives a restart.
- With a newer version in the version file, the notice appears once and `Get the new version` opens the download page in the browser.

**Adjacency:** list=applicable @ D03 T03 §2; document=not-applicable (nothing is carried or printed); settings=applicable @ D03 T03 §5; reporting=applicable @ D03 T03 §1; notifications=applicable @ D03 T03 §9; permissions=applicable @ D03 T03 §8; audit=applicable @ D03 T03 §2; exchange=not-applicable (SPEC section 15 rules out import and export); reverse=applicable @ D03 T03 §3

**Adjacency rationale:** History is both the list of clean-ups and the user's audit of what was moved and what was kept in its place. Its header reports the total freed. Every tunable is on the Settings page and names its consumer in §4. The update notice is the app's one lifecycle notice. The update check refuses any download address that is not on the allowed list. Restore reverses a clean-up.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | History view model | D03 T02 §10 | [ ] |
| 2 | §2 | History page | §1 | [ ] |
| 3 | §3 | Restore from History | §2 | [ ] |
| 4 | §4 | Settings view model | D03 T02 §10 | [ ] |
| 5 | §5 | Settings page | §4 | [ ] |
| 6 | §6 | Clear index and log folder | §5 | [ ] |
| 7 | §7 | About block and installed documents | §5 | [ ] |
| 8 | §8 | Update check | §4 | [ ] |
| 9 | §9 | Update notice and Check now | §8, §5 | [ ] |
| 10 | §10 | Shortcuts and automation names sweep | §3, §7, §9 | [ ] |
| 11 | §11 | State captures for every page | §10 | [ ] |

## 1. History view model

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/history_vm.cpp`. Done when: it lists clean-ups with their states.
2. Add the file list. Done when: it pages.

- [ ] Add `dt::app::HistoryViewModel` in `src/appcore/history_vm.cpp` loading `list_cleanups()`: per row the date, the time, `<n> photos moved to the Recycle Bin, <size>`, `<n> folders scanned`, the state text and `can_restore` (`design/SPEC.md` section 7). Done when: `tests/appcore/history_vm_tests.cpp` builds rows from a seeded index, newest first. Cheaper substitute: none needed.
- [ ] Refresh each row's state from `cleanup_state` on a background task whenever the page opens, with the texts `In Recycle Bin`, `Restored <date>`, `Partly restored` and `Recycle Bin emptied`. Done when: tests with a fake bin cover the four. Cheaper substitute: a state stored at clean-up time and never checked.
- [ ] Expose the header total `<size> freed in <n> clean-ups`, counting only photos not restored. Done when: a test with one restored clean-up leaves it out of the size. Cheaper substitute: counting restored photos as freed.
- [ ] Add `toggle_open(row)` loading the first four files (path, size, `kept <file name>`) and `and <n> more`, and `show_all(row)` paging the rest 200 at a time. Done when: tests cover a clean-up of 3, of 4 and of 327 files. Cheaper substitute: loading thousands of rows to show four.
- [ ] Expose `is_empty`. Done when: a test with no clean-up reads true. Cheaper substitute: none needed.
- [ ] Commit: `appcore: history view model`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[history-vm]"` passes, and fails when the header counts restored photos.

## 2. History page

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 7 and `design/mockups/darkroom/History.dc.html`.
**Job:** the user sees what was moved, when, and what was kept in its place.
**Treatment:** one card per clean-up with its state, opening to the list of files. Cheaper substitute that fails: a count with no file names, which gives no way to check a clean-up.
**Chrome:** a 920 wide column of `panel` cards with radius 10, a chevron button, a scrolling file list.

**Build order:**

1. Add `src/app/Pages/HistoryPage.xaml`. Done when: cards render.
2. Add the open state. Done when: files list and page.

- [ ] Add `src/app/Pages/HistoryPage.xaml`: a 920 wide column 40 below the title bar, the title `History` in `pageTitle` with the total right-aligned on its baseline in `textMuted`. Done when: a capture matches the mockup within 2 px. Cheaper substitute: none needed.
- [ ] Render each clean-up as a card 64 high when closed: a 220 wide column with the date in `bodyStrong` and the time in `caption`, the summary with the folders line under it, the state in `caption` `textMuted`, `Restore` (32 high, secondary) when `can_restore`, and a 32 x 32 chevron button named `Show files` with its expanded state exposed. Done when: a UI test with three seeded clean-ups reads three cards and finds `Restore` on the first only. Cheaper substitute: a `DataGrid`, whose chrome is not in the design.
- [ ] Open a card to its file rows: 32 high at 13, the path ellipsised in the middle, the size, and `kept <file name>` in a 150 wide column, then `and <n> more` as a link that expands to the whole list in a box at most 320 high that scrolls. Done when: a UI test opens the first card, reads four rows, expands, and scrolls to the last file. Cheaper substitute: four rows with no way to see the rest.
- [ ] Add `Open Recycle Bin` (secondary) with its note, opening the Recycle Bin through `IShell`. Done when: a UI test invokes it and the fake shell records the call. Cheaper substitute: telling the user where to look.
- [ ] Show the empty state `No clean-ups yet` with `Photos you recycle are listed here, ready to put back.` (`design/SPEC.md` section 10). Done when: a UI test on a fresh data folder reads both. Cheaper substitute: a blank page.
- [ ] Commit: `app: history page`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[history]"` passes, and fails when `Restore` shows on a clean-up whose bin was emptied.

## 3. Restore from History

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 7, the `Restore` bullet, and section 9.2 (`Undo`).
**Job:** the user changes their mind and gets the photos back where they were.
**Treatment:** one button per clean-up, progress in the card, and a notice saying how many came back. Cheaper substitute that fails: sending the user to the Recycle Bin to restore hundreds of files by hand.
**Chrome:** the card's own button, a thin progress bar in the card, the notice bar.

**Build order:**

1. Add the command. Done when: files come back.
2. Wire the two entry points. Done when: History and the result notice both restore.

- [ ] Add `restore(cleanup)` to `HistoryViewModel` running `dt::restore` on a background thread, with the card's `Restore` button replaced by a 6 px progress bar and `Putting back <i> of <n>`. Done when: a UI test recycles the fixture copies, restores, and finds every file back with its original bytes. Cheaper substitute: a frozen page.
- [ ] End with the notice `<n> photos put back.`, or `<n> photos put back. <m> were no longer in the Recycle Bin.`, or, when a file now exists at the original path, `<m> were left in the Recycle Bin because a file with the same name is there now.` Done when: UI tests cover the three. Cheaper substitute: one message for every outcome.
- [ ] Refresh the card's state after a restore, and the Review queue on its next open, since restored photos are copies again only after a new scan: add `A new scan will find them again.` to the notice when the restored clean-up belongs to the latest scan. Done when: a UI test reads the added sentence. Cheaper substitute: leaving the user to wonder why Review does not list them.
- [ ] Point the Review result notice's `Undo` at this command for its clean-up, replacing the interim behaviour of `D03 T02 §9`. Done when: the UI test of `D03 T02 §9` is updated to find the files restored after Undo. Cheaper substitute: leaving Undo as a link to History. -> XREF: D03 T02 §9
- [ ] Capture `history-none`, `history-open-in-bin`, `history-restored`, `history-partly-restored` and `history-bin-emptied`. Done when: the five PNGs exist. Cheaper substitute: none needed.
- [ ] Commit: `app: restore from history and from the result notice`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[history-restore]"` passes and leaves the Recycle Bin as it found it, and fails when a restore overwrites an existing file.

## 4. Settings view model

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/settings_vm.cpp`. Done when: every setting is exposed.
2. Name each consumer. Done when: a change reaches it.

- [ ] Add `dt::app::SettingsViewModel` in `src/appcore/settings_vm.cpp` exposing each row of the table in `design/SPEC.md` section 8 with its options and default, bound to the settings store. Done when: `tests/appcore/settings_vm_tests.cpp` changes each and reads it back from a reloaded store. Cheaper substitute: settings the page writes straight to the file.
- [ ] Wire each setting to its consumer: `Keep by default` to `suggest_keeper` (applied to undecided groups at once), `Skip photos smaller than`, `Include RAW files` and `Scan hidden folders` to `dt::ScanOptions` and the Scan page's counts, `Tell me when a new version is out` to the update check of §8. Done when: tests change each and observe the consumer: an undecided group's keeper changes, the folder count changes, the check is skipped. Cheaper substitute: a setting that is saved and read by nothing.
- [ ] Leave decided groups alone when `Keep by default` changes. Done when: a test decides a group, changes the rule, and finds its marks unchanged. Cheaper substitute: overwriting the user's decisions.
- [ ] Expose the index path and its size as text, and the model state text from a `ModelState` value (`NotDownloaded`, `Downloading(percent)`, `Ready`, `Failed`), which stays `NotDownloaded` until `D04 T01 §2` supplies it. Done when: tests cover the size text and the four state texts. Cheaper substitute: a hardcoded label.
- [ ] Commit: `appcore: settings view model`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[settings-vm]"` passes, and fails when changing the keep rule alters a decided group.

## 5. Settings page

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 8 and `design/mockups/darkroom/Settings.dc.html`.
**Job:** the user changes how DoubleTake matches, scans and checks for versions.
**Treatment:** titled groups of rows, each row a label, a one-line explanation and one control, applied at once with no Save button. Cheaper substitute that fails: a dialog with OK and Cancel, which hides whether a change took effect.
**Chrome:** `panel` cards with radius 10, rows divided by 1 px `raised` lines, `ComboBox` and `ToggleSwitch` restyled to the tokens.

**Build order:**

1. Add `src/app/Pages/SettingsPage.xaml`. Done when: it matches the mockup.
2. Bind every control. Done when: each change persists.

- [ ] Add `src/app/Pages/SettingsPage.xaml`: a 760 wide column 40 below the title bar in a vertical `ScrollViewer`, the title `Settings` in `pageTitle`, group headings in `bodyStrong`, 12 between blocks. Done when: a capture at 1280 x 1180 matches the mockup within 2 px. Cheaper substitute: a page that cannot scroll at the minimum window height.
- [ ] Build the row template: at least 68 high, 20 side padding, the label, the explanation in `caption` `textMuted`, the control on the right, each label tied to its control for UI Automation. Done when: a UI test reads each control's name as its row label. Cheaper substitute: unnamed switches.
- [ ] Add the Matching group: `Keep by default` and `Skip photos smaller than` as lists 200 wide and 32 high on `raised` with a `strokeStrong` border, and `Similar shots` as a switch with the model state text beside it. Done when: a UI test changes each list, restarts the app, and reads the choices back. Cheaper substitute: none needed.
- [ ] Add the Scanning group (`Include RAW files`, `Scan hidden folders`) and the Updates group (`Tell me when a new version is out` with `Check now` beside the switch), with switches 40 x 20, `accent` when on with an `onAccent` thumb, `textMuted` outline when off, and no On or Off text. Done when: a UI test toggles each and reads its toggle state. Cheaper substitute: the stock switch with its text label.
- [ ] Give the Similar shots switch the same behaviour as on the Scan page, both bound to the one setting: until `D04 T01 §5` ships, turning it on raises the interim notice and returns it to off. Done when: a UI test toggles it here and reads the Scan page's switch as off. Cheaper substitute: two switches that disagree. -> XREF: D04 T01 §5
- [ ] Capture `settings-defaults`. Done when: the PNG exists. Cheaper substitute: none needed.
- [ ] Commit: `app: settings page`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[settings-page]"` passes, and fails when a changed list is not saved.

## 6. Clear index and log folder

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 8 ("Your data" rows) and section 9.5.
**Job:** the user starts afresh, or finds the logs to send with a problem report.
**Treatment:** the index's path and size with a `Clear index` button that asks first, and a button that opens the log folder. Cheaper substitute that fails: telling the user to delete a file in a hidden folder.
**Chrome:** two rows in a `panel` card, secondary buttons, the `DtDialog` frame.

**Build order:**

1. Add the two rows. Done when: they match the mockup.
2. Add the clear flow. Done when: the index is emptied after a yes.

- [ ] Add the `Your data` group: `Scan index` with the path, the size and the explanation, and `Clear index`; `Log files` with `Open log folder`. Done when: a UI test reads the path as the test's data folder. Cheaper substitute: none needed.
- [ ] Ask with a dialog: `Clear the scan index?`, `The next scan will read every photo again. Your photos and History are not touched.`, buttons `Clear index` and `Cancel`. Done when: a UI test cancels and finds the index unchanged. Cheaper substitute: clearing on one click.
- [ ] On confirm, clear the `files`, `scans`, `groups` and `members` tables and the undo log, keep `cleanups` and `cleanup_files`, disable the Review tab, and show the notice `Index cleared.` Done when: a UI test clears, then finds History still listing its clean-up and Review disabled. Cheaper substitute: `dt::Index::clear()` as it stands, which would wipe History; add `clear_scan_data()` to the engine with a test.
- [ ] Refuse to clear while a scan runs, with the notice `Wait for the scan to finish, or cancel it first.` Done when: a UI test confirms the refusal. Cheaper substitute: clearing tables a scan is writing.
- [ ] Wire the same `Clear index` action to the problem notice shown when the index cannot be opened (`D02 T01 §9`): there it renames the bad file aside and creates a new index. Done when: a UI test with a corrupt index clears it and can scan. Cheaper substitute: a notice whose action does nothing.
- [ ] Capture `dialog-clear-index`. Done when: the PNG exists. Cheaper substitute: none needed.
- [ ] Commit: `app: clear index and log folder`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[settings-data]"` passes, and fails when clearing the index removes History.

## 7. About block and installed documents

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 8, last bullet, and the About card of `design/mockups/darkroom/Settings.dc.html`.
**Job:** the user sees which version they have, under what licence, and where the project lives.
**Treatment:** the icon, the name and version, the licence line and four links. Cheaper substitute that fails: an About dialog reached from nowhere.
**Chrome:** a `panel` card with the icon at 56 and `HyperlinkButton`s in `accent`.

**Build order:**

1. Add the card. Done when: it shows the real version.
2. Wire the links. Done when: each opens its target.

- [ ] Add the About card: the icon at 56 from `resources/brand/`, `DoubleTake <version>` in `bodyStrong` from `$(DoubleTakeVersion)`, the line `Free software under the GNU General Public License, version 3.` in `caption`. Done when: a UI test reads the version equal to `dt::version()`. Cheaper substitute: a version typed into the XAML.
- [ ] Add `dt::app::Links` in `src/appcore/links.cpp` holding the website and source addresses as build properties (`DoubleTakeWebsiteUrl`, `DoubleTakeSourceUrl`) set in `version.props`, the website defaulting to the source repository until the owner supplies it (foundation plan section 11). Done when: a test reads both and both are `https`. Cheaper substitute: addresses typed in several files. -> XREF: D99 T01 §1
- [ ] Add the four links: `Website` and `Source code` open in the browser through `IShell`; `Licence` and `Third-party notices` open `LICENSE.txt` and `NOTICE.txt` from the folder the executable is in. Done when: a UI test invokes each and the fake shell records two addresses and two existing file paths. Cheaper substitute: links to files that are not installed.
- [ ] Copy `LICENSE` and `NOTICE.md` beside the executable as `LICENSE.txt` and `NOTICE.txt` in a post-build step. Done when: both exist under `build\bin\x64\Debug\`. Cheaper substitute: fetching the licence from the internet.
- [ ] Commit: `app: about block and installed documents`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[about]"` passes, and fails when `LICENSE.txt` is missing beside the executable.

## 8. Update check

The version check, with no window: read a small file, compare, and trust only known hosts.

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/update.cpp`. Done when: versions compare correctly.
2. Add the fetch. Done when: every failure is quiet and safe.

- [ ] Add `dt::app::parse_version(text)` and `compare` for `major.minor.patch` numbers in `src/appcore/update.cpp`. Done when: `tests/appcore/update_tests.cpp` covers `0.2.0` over `0.1.9`, `0.10.0` over `0.9.0`, equal versions, and malformed text refused. Cheaper substitute: comparing strings, which puts `0.10.0` below `0.9.0`.
- [ ] Add `dt::app::parse_version_file(json)` reading `version` and `url`, refusing a file over 4 KB, a missing field, a `url` that is not `https`, and a `url` whose host is not on the allowed list (`github.com` under the project's path, and the website host from `dt::app::Links`) (foundation plan section 6). Done when: tests cover each refusal and one accepted file. Cheaper substitute: opening whatever address the file names, which lets a tampered file send users to any site.
- [ ] Add `IHttp`'s real implementation with `Windows.Web.Http.HttpClient` in `src/app/`, with a 10 second limit, no cookies, no cache, and a user agent of `DoubleTake/<version>` only. Done when: a UI-free test against a local listener gets the body and times out on a stalled one. Cheaper substitute: WinINet with default caching, which can serve an old file.
- [ ] Add `UpdateChecker::check()` fetching the address in the build property `DoubleTakeUpdateUrl` (default `https://raw.githubusercontent.com/rizonetech/DoubleTake/main/version.json`, foundation plan D12), returning `Newer(version, url)`, `Current` or `Failed(reason)`, and logging the result. Done when: tests with the fake `IHttp` cover the three, and a body that is HTML is `Failed`. Cheaper substitute: treating any failure as "current" with no log line.
- [ ] Send nothing about the user or the machine: the request has no query string and no identifying header. Done when: a test inspects the fake's recorded request. Cheaper substitute: a version or machine identifier in the address, which is tracking.
- [ ] Commit: `appcore: update check`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[update]"` passes, and fails when a `url` on an unknown host is accepted.

## 9. Update notice and Check now

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 9.4, section 8 (`Check now`), and the notice in `design/mockups/darkroom/Dialogs.dc.html`.
**Job:** the user learns a new version exists and reaches the download page in one click.
**Treatment:** a notice bar under the title bar on every page with one amber action that opens the browser. Cheaper substitute that fails: downloading or installing the update in the app, which decision D7 rules out.
**Chrome:** the notice bar in its `Update` kind.

**Build order:**

1. Run the check at start. Done when: the notice appears for a newer version.
2. Add dismiss and Check now. Done when: both behave as the SPEC says.

- [ ] Run `UpdateChecker::check()` once after the window is shown, off the UI thread, when the setting is on and `--no-update-check` is absent. Done when: a UI test with the address pointed at a local file through the test hook sees the check, and sees none with the switch. Cheaper substitute: a check that delays the window appearing.
- [ ] On `Newer`, show the `Update` notice on every page: `DoubleTake <new> is out.` in `bodyStrong`, `You have <current>. The download page opens in your browser.`, the action `Get the new version`, and `Dismiss`. Done when: a UI test reads the texts on Scan and again after switching to History. Cheaper substitute: a notice on one page only.
- [ ] `Get the new version` opens the file's `url` through `IShell` and leaves the notice in place. Done when: a UI test invokes it and the fake shell records the address. Cheaper substitute: starting a download.
- [ ] `Dismiss` stores that version in the settings and the notice does not return for it, on this run or the next; a still newer version shows again. Done when: a UI test dismisses `0.2.0`, restarts and sees no notice, then sees one for `0.3.0`. Cheaper substitute: a notice that returns on every start.
- [ ] `Check now` runs the check regardless of the setting and the dismissed version, disables itself meanwhile, and answers with the update notice, `You have the newest version.` or `Could not check. Try again later.` Done when: UI tests cover the three. Cheaper substitute: a button with no answer when nothing is new.
- [ ] Show nothing on a failed automatic check. Done when: a UI test with an unreachable address finds no notice and one log line. Cheaper substitute: an error at every start for a user who is offline.
- [ ] Capture `notice-update` and `notice-problem`. Done when: both PNGs exist. Cheaper substitute: none needed.
- [ ] Commit: `app: update notice and check now`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[update-notice]"` passes, and fails when a dismissed version's notice returns after a restart.

## 10. Shortcuts and automation names sweep

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 11, every bullet, and section 12.
**Job:** a keyboard or screen reader user can do everything a pointer user can.
**Treatment:** every control named and reachable in reading order, with the shortcuts of section 11. Cheaper substitute that fails: checking the two pages a tester happens to open.
**Chrome:** no new chrome; this section audits and repairs what the earlier sections built.

**Build order:**

1. Add an automation audit test. Done when: it walks every page.
2. Repair what it finds. Done when: it passes.

- [ ] Add `tests/ui/a11y_tests.cpp` walking the UI Automation tree of each page and dialog and failing on any focusable control with an empty name, any image with no name that is not marked decorative, and any two controls on a page with the same name and type. Done when: the test runs over Scan, Scanning, Review, History, Settings and each dialog. Cheaper substitute: a manual check that is done once and never again.
- [ ] Add a tab-order test per page recording the order of focus stops and comparing it with the reading order in `tests/ui/tab_order.json`. Done when: the recorded order of each page is top to bottom, left to right, and committed. Cheaper substitute: an order that jumps between panes.
- [ ] Add a contrast test reading each text element's foreground and background from a capture and failing below 4.5 to 1, or 3 to 1 for text of 24 px and larger. Done when: it passes on the captures of §11, with any failing token fixed in `design/tokens.json` and the SPEC in the same commit. Cheaper substitute: trusting the token table.
- [ ] Verify `F5` on Scan, `Esc` on Scanning, the Review keys, and that no Review key acts in a text field or behind a dialog. Done when: a UI test covers each. Cheaper substitute: none needed.
- [ ] Verify every string on screen comes from `resources/strings/en-GB.json`: a test build with every string wrapped in brackets shows no unwrapped text in the captures' automation trees. Done when: the walk finds no control whose name lacks the brackets. Cheaper substitute: strings typed into XAML.
- [ ] Commit: `tests: shortcuts, names, tab order and contrast for every page`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[a11y]"` passes, and fails when a button's automation name is removed.

## 11. State captures for every page

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 14, every row.
**Job:** a reviewer can compare each state of the app with its mockup without running it.
**Treatment:** one PNG per state in `build/renders/`, produced by one command, with a contact sheet. Cheaper substitute that fails: a handful of hand-made screenshots that go stale.
**Chrome:** no new chrome; this section captures what exists.

**Build order:**

1. Add the capture run. Done when: one command writes every state.
2. Add the window states. Done when: section 14 is covered row by row.

- [ ] Add `scripts/capture-all.ps1` running the UI tests tagged `[capture]` and checking that every state named in `design/SPEC.md` section 14 has a PNG, listing any that is missing. Done when: it exits 0 with every state present, and 1 when one is removed. Cheaper substitute: a count of files, which passes with the wrong files.
- [ ] Add the window states: `window-min-size` (1024 x 680), `window-maximised`, `window-text-200` and `window-contrast` for the Review page. Done when: the four PNGs exist and the queue is 248 wide in each. Cheaper substitute: only the default size.
- [ ] Add `settings-model-downloading` and `settings-model-ready` through the test hook's model state. Done when: both PNGs exist. Cheaper substitute: none needed.
- [ ] Write `build/renders/index.html`, a contact sheet listing each capture beside its state name and the SPEC section it belongs to. Done when: the file opens and shows every capture. Cheaper substitute: a folder of unnamed images.
- [ ] Compare each default-size capture with its mockup's measurements: title position, column width, panel positions and control heights within 2 px, recorded in `docs/reviews/design-fidelity.md` with any deliberate difference explained. Done when: the document has a row per page and no unexplained difference. Cheaper substitute: "looks about right".
- [ ] Commit: `tests: captures of every state in the SPEC`

**Test checkpoint:** `pwsh scripts/capture-all.ps1` exits 0 and writes every state in `design/SPEC.md` section 14, and exits 1 when a state has no capture.

## Verification

- On the build machine: a clean-up made in Review appears in History and is restored from there; each setting changed in Settings is in effect after a restart; with a newer `version.json` served locally the notice appears, opens the download address, and stays dismissed.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
