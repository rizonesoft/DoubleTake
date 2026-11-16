---
schema_version: 1
id: review-page
domain: 03-screens
status: active
title: "TODO-02 -- Review page"
depends_on: ["application-shell", "scan-pages"]
---

# TODO-02 -- Review page

> **Goal:** The Review page of `design/SPEC.md` section 6 works on real photos: the queue, the two compare panes with their values, the member strip, every key and tag action, undo, actual size, the footer totals, the recycle dialog with its progress and result, and the empty and edge states.

> **Current state:** Measured 2026-11-16. A scan ends on an empty Review page (`D03 T01 §6`). The engine stores groups, marks, decisions and undo (`D01 T02 §4`, `§5`), runs clean-ups (`D01 T02 §8`) and decodes any supported photo at a requested size (`D01 T01 §3` to `§5`). The dialog frame and notice bar exist (`D02 T01 §8`).

## Inputs

- `design/SPEC.md` sections 6, 9.1, 9.2, 10, 11 and 12.
- `design/mockups/darkroom/Review.dc.html` and `Dialogs.dc.html`.
- `docs/plans/2026-11-16-doubletake-foundation.md` sections 5.4, 5.5, 5.7 and 6 (called "the foundation plan" below).
- -> XREF: D03 T01 §6 -- a finished scan lands here, and the empty states of §10 are what it shows with no groups
- -> XREF: D03 T03 §3 -- the result notice's Undo in §9 calls the restore built there
- -> XREF: D04 T01 §6 -- Similar groups appear in the queue of §4 after the duplicate groups

## Outcome

- After scanning the fixtures, pressing the Left arrow through every group, then `Recycle marked` and `Move to Recycle Bin`, leaves only the keepers on disk and a clean-up in History.
- Every Review and dialog state in `design/SPEC.md` section 14 has a capture in `build/renders/`.

**Adjacency:** list=applicable @ D03 T02 §4; document=not-applicable (nothing is carried or printed); settings=not-applicable (the keep rule is set on the Settings page, D03 T03 §5); reporting=applicable @ D03 T02 §9; notifications=applicable @ D03 T02 §9; permissions=applicable @ D03 T02 §7; audit=not-applicable (clean-ups are recorded by the engine, D01 T02 §8); exchange=not-applicable (SPEC section 15 rules out import and export); reverse=applicable @ D03 T02 §2

**Adjacency rationale:** The queue is the list of groups. The footer totals and the dialog's two rows summarise what will be recycled, and the result notice reports what was. The refusal is the rule that a group keeps at least one photo, shown as a notice in §7. Undo in §2 reverses a decision, and the result notice's Undo reverses a clean-up.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Review view model: queue and current group | D03 T01 §6 | [ ] |
| 2 | §2 | Review view model: decisions, undo and totals | §1 | [ ] |
| 3 | §3 | Photo loading for panes and thumbnails | D02 T01 §4 | [ ] |
| 4 | §4 | Queue pane | §1, §3 | [ ] |
| 5 | §5 | Compare panes and their values | §4 | [ ] |
| 6 | §6 | Member strip | §5 | [ ] |
| 7 | §7 | Keys, tags and the context menu | §2, §6 | [ ] |
| 8 | §8 | Actual size with panes panning together | §5 | [ ] |
| 9 | §9 | Footer, recycle dialog and result notice | §7 | [ ] |
| 10 | §10 | Empty and edge states | §9 | [ ] |

## 1. Review view model: queue and current group

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/appcore/review_vm.cpp`. Done when: it lists groups and holds a current one.
2. Add the pane model. Done when: left and right follow the rules.

- [ ] Add `dt::app::ReviewViewModel` in `src/appcore/review_vm.cpp` loading the latest scan's groups: `queue` rows (group id, number, `<n> <kind>, <size>` text, decided flag, the two thumbnail paths), `header_text` (`214 groups, largest first`) and `done_text` (`11 done`) (`design/SPEC.md` section 6, Queue). Done when: `tests/appcore/review_vm_tests.cpp` builds the rows from a seeded index in bytes-to-recover order. Cheaper substitute: loading every member of every group at once, which is slow at thousands of groups.
- [ ] Add `current` with the opening rule: the first undecided group, or the first group when all are decided; `select(group)`, `next()` and `previous()` move without deciding. Done when: tests cover opening, moving past both ends (which stays put), and reopening the app on the same group. Cheaper substitute: always opening on group 1.
- [ ] Add the pane model: `left` is the keeper (suggested or decided), `right` the next member in the group's order; `show(member)` puts a non-keeper on the right and the keeper on the left. Done when: tests cover a group of two and of four. Cheaper substitute: showing the first two files regardless of the keeper.
- [ ] Expose for the current group the title (`Group 12 of 214`), the summary (`Resized copy, 3 photos, 98% alike`, with the kind names of `design/SPEC.md` section 6 and the likeness of the two on show), and per pane the file name, tag, and the four values with a `better` flag on resolution and file size where the two differ. Done when: tests check the text and flags for each kind. Cheaper substitute: marking the keeper's values better even when they are equal.
- [ ] Commit: `appcore: review view model, queue and panes`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[review-vm]"` passes, and fails when the queue is not ordered by bytes to recover.

## 2. Review view model: decisions, undo and totals

**Phase:** 3
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add the decision commands. Done when: each writes marks through the engine.
2. Add undo and totals. Done when: both follow the index.

- [ ] Add `keep_left()`, `keep_right()`, `keep_both()`, `skip()`, `toggle(member)` and `accept_all()` calling the engine's decision functions and `set_marks`, then moving to the next undecided group (`design/SPEC.md` section 6, table). Done when: tests check the marks and the new current group for each, and that `skip` writes nothing. Cheaper substitute: marks held in the view model until a later save.
- [ ] Surface the engine's last-keeper refusal as the notice `Every group keeps at least one photo.` and leave the marks unchanged. Done when: a test toggles a group's only keeper and reads the notice. Cheaper substitute: silently ignoring the click.
- [ ] Add `undo()` restoring the previous marks of the last decision from the engine's undo log and selecting its group; `can_undo` is false with nothing to undo. Done when: tests decide three, undo three, and find `can_undo` false. Cheaper substitute: undo that only steps the selection back.
- [ ] Run `accept_all()` on a background task with progress to the notice bar, in one index transaction per 200 groups. Done when: a test over 5,000 groups finishes and every group is decided as suggested. Cheaper substitute: a frozen window.
- [ ] Expose `marked_text` (`27 photos marked, 412 MB`) and `can_recycle` from `marked_totals`, and an announcement string after each decision (`Kept left. Group 13 of 214.`). Done when: tests check both after each command. Cheaper substitute: totals that count suggestions.
- [ ] Commit: `appcore: review decisions, undo and totals`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[review-decide]"` passes, and fails when `undo` does not restore the marks.

## 3. Photo loading for panes and thumbnails

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** no

**Build order:**

1. Add `src/app/Imaging/PhotoLoader.cpp`. Done when: any supported photo becomes an image source.
2. Add the cache. Done when: memory is bounded.

- [ ] Add `PhotoLoader::thumbnail(path, size)` in `src/app/Imaging/PhotoLoader.cpp` using `IShellItemImageFactory` off the UI thread, falling back to the engine decoder when the shell has no thumbnail (foundation plan section 6). Done when: a UI test shows thumbnails for a JPEG, the HEIC sample and a DNG sample. Cheaper substitute: full decodes for every queue row.
- [ ] Add `PhotoLoader::photo(path, longestSide)` decoding through `dt::decode` on a background thread into a `SoftwareBitmapSource`, cancellable when the user moves on. Done when: a UI test moving quickly through ten groups ends showing the tenth group's photos. Cheaper substitute: letting stale decodes land over the current photo.
- [ ] Add a cache of decoded photos bounded at 64 MB, least recently used out first, and decode the next group's two photos ahead. Done when: a test of the cache with 100 MB of images holds at most 64 MB. Cheaper substitute: an unbounded cache.
- [ ] Show a neutral `panel` tile while loading and `This photo is no longer there` when the file is missing (`design/SPEC.md` section 10). Done when: a UI test deletes a file on show and reads the text. Cheaper substitute: a blank pane.
- [ ] Commit: `app: photo loading and cache`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[photo-loader]"` passes, and fails when the cache bound is removed.

## 4. Queue pane

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 6, Queue, and the `aside` of `design/mockups/darkroom/Review.dc.html`.
**Job:** the user sees how many groups there are, which are done, and jumps to any of them.
**Treatment:** a fixed 248 wide list of 64 high rows with a pair of overlapping thumbnails, and one button to accept every suggestion. Cheaper substitute that fails: a number with next and previous buttons, which hides what is coming.
**Chrome:** a virtualised `ItemsRepeater` in a `ScrollViewer`, rows as buttons with radius 8, a secondary button at the bottom.

**Build order:**

1. Add `src/app/Pages/ReviewPage.xaml` with the queue. Done when: rows render from the view model.
2. Add states and the accept button. Done when: current and decided rows differ.

- [ ] Add `src/app/Pages/ReviewPage.xaml` with the queue column: 248 wide, a 1 px `raised` right line, 12 x 8 padding, the header line in `caption` with `done_text` right-aligned. Done when: UI Automation reports the column 248 wide at every window size. Cheaper substitute: a resizable splitter the SPEC does not have.
- [ ] Render rows with a virtualising `ItemsRepeater`: 64 high, radius 8, 4 apart, the overlapping pair of 46 x 34 thumbnails (the back one at 60% opacity, the front with a 2 px ring in the row's background), the group name in `bodyStrong` and the summary in `caption`. Done when: a UI test with 5,000 groups scrolls to the end and the process's memory stays under 400 MB. Cheaper substitute: a `StackPanel` holding every row.
- [ ] Draw the current row with a `raised` fill and an 8 px `accent` dot, and a decided row with a tick in place of the dot and its text in `textMuted`. Done when: a UI test decides a group and reads the row's `decided` automation state. Cheaper substitute: colour as the only sign a row is done.
- [ ] Keep the current row scrolled into view as the user moves with the keys. Done when: a UI test pressing Down 30 times finds the current row's bounding box inside the queue. Cheaper substitute: a selection that walks out of sight.
- [ ] Add `Accept every suggestion` (32 high, secondary, full width) at the bottom, asking first with a `DtDialog`: `Accept every suggestion?`, `<n> groups will be decided as suggested. You can still change any of them.`, buttons `Accept` and `Cancel`. Done when: a UI test accepts and finds `done_text` equal to the group count. Cheaper substitute: deciding hundreds of groups on one stray click.
- [ ] Commit: `app: review queue pane`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-queue]"` passes, and fails when a decided row has no tick.

## 5. Compare panes and their values

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 6, Stage, first four bullets, and the `main` of `design/mockups/darkroom/Review.dc.html`.
**Job:** the user sees two copies side by side and which one is better.
**Treatment:** two equal panes with a large photo, a KEEP or RECYCLE tag, the file name and four values, the better value in amber and heavier. Cheaper substitute that fails: one photo at a time, which makes the user remember the other.
**Chrome:** a two-column grid, photos fitted inside radius 10 frames, tags as small filled labels, a definition list of values.

**Build order:**

1. Add the stage header and panes. Done when: they match the mockup.
2. Bind the values. Done when: better values are marked.

- [ ] Add the stage: 20 top and 24 side padding, the title in `groupTitle` with the summary in `textMuted` on its baseline, then a two-column grid 20 apart. Done when: a capture matches the mockup within 2 px at 1280 x 800. Cheaper substitute: panes of unequal width.
- [ ] Add each pane's photo frame: 300 high at the default window height, growing with the window, radius 10, `panel` behind, the photo fitted whole inside with no cropping. Done when: a UI test with a portrait and a landscape photo finds both whole inside their frames. Cheaper substitute: cropping to fill, which hides the difference between a photo and its crop.
- [ ] Add the keeper's 3 px `accent` outline inside the frame, and the tag at 14 from the top left: `KEEP` on `accent` with `onAccent` text, `RECYCLE` on `ground` with `text`, 28 high, radius 6, in the `tag` style. Done when: a UI test reads each pane's tag text. Cheaper substitute: an outline alone, which is colour only.
- [ ] Add the file name in `bodyStrong` and the four rows (`Resolution`, `File size`, `Taken`, `Folder`) with labels 96 wide in `textMuted` at 13, the folder ellipsised in the middle with the full path as tooltip. Done when: a UI test reads the eight values of the fixture group. Cheaper substitute: the full path on one line, pushing the layout wide.
- [ ] Draw a value flagged `better` in `accent` at weight 600 and others in `text` at 400. Done when: a UI test on a resized pair reads the larger resolution's `better` automation property and not the other's. Cheaper substitute: colouring every keeper value.
- [ ] Name each pane for UI Automation with its file name, tag and four values in one string. Done when: a UI test reads the left pane's name. Cheaper substitute: unnamed images.
- [ ] Capture `review-undecided` and `review-decided`. Done when: both PNGs exist and differ. Cheaper substitute: none needed.
- [ ] Commit: `app: review compare panes`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-panes]"` passes, and fails when equal values are drawn as better.

## 6. Member strip

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 6, Stage, last bullet, and the strip in `design/mockups/darkroom/Review.dc.html`.
**Job:** in a group of more than two, the user sees every copy and chooses which to compare.
**Treatment:** a row of 96 x 72 thumbnails with their tags, the two on show outlined. Cheaper substitute that fails: comparing only the first two and recycling the rest unseen.
**Chrome:** a horizontal list of buttons with radius 6, scrolling sideways when it overflows.

**Build order:**

1. Add the strip. Done when: it lists the group's members.
2. Wire selection. Done when: choosing a member changes a pane.

- [ ] Add the strip under the panes: the label `All <n> in this group` 96 wide in `caption`, then a thumbnail button per member, 12 apart, each with its tag at the bottom left (18 high, 10 px). Done when: a UI test on a group of three finds three members and their tags. Cheaper substitute: hiding the strip, so a third copy is never seen.
- [ ] Outline the two on show with a 2 px line offset 2 px: the keeper in `accent`, the other in `text`. Done when: a UI test reads the `shown` state of each member. Cheaper substitute: no sign of which members are in the panes.
- [ ] Choosing a member calls `show(member)`. Done when: a UI test clicks the third member and the right pane's name changes to it. Cheaper substitute: a strip that is decoration.
- [ ] Hide the strip for a group of two, and scroll it sideways with the selection kept in view when members overflow the width. Done when: a UI test with a group of 12 scrolls to the last member. Cheaper substitute: members cut off at the edge.
- [ ] Capture `review-group-of-three`. Done when: the PNG shows the strip. Cheaper substitute: none needed.
- [ ] Commit: `app: review member strip`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-strip]"` passes, and fails when choosing a member does not change the right pane.

## 7. Keys, tags and the context menu

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 6, "Deciding a group" and its table, and section 11.
**Job:** the user decides a group with one key and moves on.
**Treatment:** arrow keys keep a side, `B` keeps both, `S` skips, `Ctrl+Z` undoes, and a click on a tag switches it. Cheaper substitute that fails: mouse-only buttons, which make hundreds of groups slow.
**Chrome:** keyboard accelerators on the page, tags as buttons, a standard context menu.

**Build order:**

1. Add the keys. Done when: each calls its command.
2. Add tag clicks and the menu. Done when: both work by pointer and keyboard.

- [ ] Add page accelerators: Left, Right, `B`, `S`, `Ctrl+Z`, Up, Down and Enter, mapped to the view model commands of the table in `design/SPEC.md` section 6, active when focus is in the stage or the queue and never while a dialog is open or a text field has focus. Done when: a UI test sends each key and checks the marks or the current group. Cheaper substitute: keys that fire behind an open dialog.
- [ ] Make each pane's tag a button that calls `toggle(member)`, named `<file name>, KEEP` or `RECYCLE`, and do the same for strip tags. Done when: a UI test invokes the right tag and finds the group decided with both marked KEEP. Cheaper substitute: tags that are labels only.
- [ ] Show the refusal notice when a toggle would leave no keeper. Done when: a UI test on a group of two toggles the keeper after the other is RECYCLE and reads `Every group keeps at least one photo.` Cheaper substitute: none needed.
- [ ] Announce each decision through a live region with the view model's announcement string. Done when: a UI test reads `Kept left. Group 2 of` after the Left key. Cheaper substitute: a silent change a screen reader user cannot follow.
- [ ] Add each pane's context menu, by right click and by the menu key: `Open`, `Show in folder`, `Copy path`, through `IShell` and the clipboard. Done when: a UI test invokes each and checks the fake shell and the clipboard text. Cheaper substitute: no way to reach the file.
- [ ] Commit: `app: review keys, tags and context menu`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-keys]"` passes, and fails when the Left key acts while a dialog is open.

## 8. Actual size with panes panning together

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 6, table row `Actual size`.
**Job:** the user checks which copy is sharper.
**Treatment:** `Z` switches both panes between fitted and one photo pixel per screen pixel, and dragging either pans both. Cheaper substitute that fails: zooming one pane, which compares different parts of the picture.
**Chrome:** two `ScrollViewer`s with their offsets tied, and the fitted view as the default.

**Build order:**

1. Add the two view modes. Done when: `Z` switches both.
2. Tie the panning. Done when: both show the same region.

- [ ] Add `actual_size` to the view model and bind both panes: fitted, or 100% with the full-resolution decode requested from `PhotoLoader` for the visible photos only. Done when: a UI test presses `Z` and reads the left photo's scale as 1. Cheaper substitute: upscaling the fitted bitmap, which shows blur instead of detail.
- [ ] Tie the two scroll positions by fraction of each photo's size, so photos of different pixel sizes show the same region, and pan by pointer drag and arrow keys with Shift. Done when: a UI test pans the left pane to its bottom right and finds the right pane at its bottom right. Cheaper substitute: tying raw pixel offsets, which drifts on a resized pair.
- [ ] Return to fitted when the group changes, and on a second `Z`. Done when: a UI test confirms both. Cheaper substitute: staying zoomed into the next group's corner.
- [ ] Capture `review-actual-size`. Done when: the PNG exists. Cheaper substitute: none needed.
- [ ] Commit: `app: review actual size with tied panning`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-zoom]"` passes, and fails when the panes pan separately.

## 9. Footer, recycle dialog and result notice

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 6, Footer, and sections 9.1 and 9.2, with `design/mockups/darkroom/Dialogs.dc.html`.
**Job:** the user moves the marked copies to the Recycle Bin, knowing how many and how much.
**Treatment:** a footer showing the running total and one amber button, a dialog that states the count and the space, progress with Stop, and a result notice with Undo. Cheaper substitute that fails: recycling on each key press with no summary and no undo.
**Chrome:** a 56 high footer with key caps, the `DtDialog` frame, the notice bar.

**Build order:**

1. Add the footer. Done when: totals follow decisions.
2. Add the dialog flow. Done when: files move and the result shows.

- [ ] Add the footer: 56 high, a 1 px `raised` top line, key caps (22 high, radius 4, `strokeStrong` border) with their hints in `caption`, then `marked_text` at 14, then `Recycle marked` (36 high, radius 8, `accent`), disabled when `can_recycle` is false. Done when: a UI test decides one group and reads the new total and an enabled button. Cheaper substitute: a button enabled with nothing marked.
- [ ] Open the recycle dialog with the title `Move <n> photos to the Recycle Bin?`, the explanation, and the two rows (`<n> in <g> groups`, and the size in `accent`), buttons `Move to Recycle Bin` and `Cancel`. Done when: a UI test reads the four texts and cancels with nothing moved. Cheaper substitute: a yes or no box with no numbers.
- [ ] On confirm run `dt::clean_up` on a background thread with the dialog showing a progress bar, `Moving <i> of <n>` and `Stop` as its only button; Stop cancels between files. Done when: a UI test on a copy of the fixtures finds the marked files gone from their folders. Cheaper substitute: a frozen dialog.
- [ ] Show the result notice: `<n> photos moved to the Recycle Bin. <size> will be freed when you empty it.`, or with skipped files `<n> photos moved. <m> had changed since the scan and were left alone.`, with the action `Undo`. Done when: a UI test edits one marked file before confirming and reads the second wording. Cheaper substitute: reporting the planned count instead of the real one.
- [ ] Reload the queue after a clean-up so recycled groups are gone, and select the next undecided group. Done when: a UI test finds the queue shorter by the groups recycled. Cheaper substitute: rows for files that no longer exist.
- [ ] Wire the notice's `Undo` to restore that clean-up through the restore command of `D03 T03 §3`; until that section ships, the action opens History. Done when: a UI test invokes Undo and lands on History. Cheaper substitute: an Undo that does nothing. -> XREF: D03 T03 §3
- [ ] Capture `dialog-recycle` and `dialog-recycle-progress`. Done when: both PNGs exist. Cheaper substitute: none needed.
- [ ] Commit: `app: review footer, recycle dialog and result`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-recycle]"` passes and leaves the Recycle Bin as it found it, and fails when a file changed since the scan is moved.

## 10. Empty and edge states

**Phase:** 3
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 10, the three Review rows.
**Job:** the user is told plainly when there is nothing to review, when everything is done, and when a photo has gone.
**Treatment:** a centred title, one line and one button in place of the queue and stage. Cheaper substitute that fails: an empty queue and blank panes.
**Chrome:** a centred column in the page, with the `pageTitle` style and a secondary button.

**Build order:**

1. Add the two empty states. Done when: each shows in its case.
2. Handle a missing photo. Done when: the group repairs itself.

- [ ] Show `No duplicates found`, `<n> photos, every one different.` and `Scan again` (which opens Scan) when the latest scan has no groups. Done when: a UI test scanning a folder with no copies reads the three. Cheaper substitute: none needed.
- [ ] Show `All done`, `<n> photos moved to the Recycle Bin.` and `Open History` when every group has been decided and recycled. Done when: a UI test completes the fixtures and reads the three. Cheaper substitute: an empty list with no word of what happened.
- [ ] When a photo on show is missing, show `This photo is no longer there`, remove that member from the group in the index, and remove the group when one member is left. Done when: a UI test deletes a member's file outside the app, selects the group, and finds the member gone from the strip. Cheaper substitute: offering to recycle a file that is not there.
- [ ] Re-check the current group's files when the window regains focus. Done when: a UI test deletes a file while the app is in the background and finds the state updated on return. Cheaper substitute: stale panes.
- [ ] Capture `review-nothing-found` and `review-all-done`. Done when: both PNGs exist. Cheaper substitute: none needed.
- [ ] Commit: `app: review empty and edge states`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[review-states]"` passes, and fails when a missing member is still listed in the strip.

## Verification

- On a copy of the fixtures, a full pass by keyboard only (arrows, `B`, `S`, `Ctrl+Z`, then `Recycle marked`) leaves the keepers on disk, shows the result notice, and ends on `All done`.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
