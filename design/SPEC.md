# DoubleTake interface specification

Direction: **Darkroom**, chosen by the owner on 2026-11-16 from three explorations. This file is the source of truth for the interface. Where a mockup and this file disagree, this file wins and the mockup is corrected.

Mockups are in [`mockups/darkroom/`](mockups/darkroom/): one `.dc.html` file per screen, every measurement written as an inline style. Colours and sizes are in [`tokens.json`](tokens.json). The photographs in the mockups are drawn placeholders and are not part of the design.

## 1. Principles

1. Photos carry the colour. The interface is dark and neutral, and only one accent exists.
2. Amber means "the one to keep" or "the main action", and nothing else. It never decorates.
3. Compare first. The Review screen shows two photos large and side by side, and one key decides a group.
4. Nothing is deleted. Unwanted copies go to the Recycle Bin, every group keeps at least one photo, and History can put a clean-up back.
5. Meaning never rests on colour alone: KEEP and RECYCLE are words, and the better value is also heavier type.
6. Everything runs on the PC. The only network use is the version check (section 9.4) and the one-time model download (section 9.3).

## 2. Tokens

`tokens.json` holds the values. The names below are used throughout this file.

| Token | Value | Use |
| --- | --- | --- |
| `ground` | `#141312` | Window background, segmented control track, dialog footer |
| `panel` | `#1E1C1A` | Cards, drop zone, dialog body |
| `raised` | `#292623` | Buttons, chips, selected queue row, notice bar, hairlines |
| `stroke` | `#3A3632` | Dialog border |
| `strokeStrong` | `#5A544D` | Button and key-cap borders, drop zone dashes |
| `text` | `#F2EEE8` | Primary text |
| `textMuted` | `#B5ADA2` | Secondary text, idle tabs, off switches |
| `accent` | `#F5A524` | Keeper, main action, active tab line, better value, progress |
| `accentHover` | `#FFC562` | Accent on pointer over |
| `onAccent` | `#1A1408` | Text and glyphs on accent |
| `scrim` | `#0A0A09` at 70% | Behind a dialog |

Type: `Space Grotesk` (bundled, SIL Open Font License) for the wordmark, page titles, large numbers and dialog titles; `Segoe UI Variable Text` for everything else.

| Style | Font | Size | Weight | Tracking |
| --- | --- | --- | --- | --- |
| `pageTitle` | Space Grotesk | 40 | 700 | -0.03em |
| `bigNumber` | Space Grotesk | 56 | 700 | -0.03em |
| `groupTitle` | Space Grotesk | 24 | 700 | -0.02em |
| `dialogTitle` | Space Grotesk | 22 | 700 | -0.02em |
| `wordmark` | Space Grotesk | 15 | 700 | -0.02em |
| `stat` | Segoe UI Variable Text | 24 | 600 | 0 |
| `body` | Segoe UI Variable Text | 14 | 400 | 0 |
| `bodyStrong` | Segoe UI Variable Text | 14 | 600 | 0 |
| `table` | Segoe UI Variable Text | 13 | 400 | 0 |
| `caption` | Segoe UI Variable Text | 12 | 400 | 0 |
| `tag` | Segoe UI Variable Text | 12 | 700 | 0.06em, upper case |

Shape: radius 10 on panels and compare photos, 8 on the two large accent buttons, 6 on controls, tags and strip thumbnails, 4 on queue thumbnails and key caps. Sizes sit on a 4 px grid. Control height is 32, except the dialog buttons and footer button (36) and Start scan (44).

## 3. Window and title bar

- Opens at 1280 x 800 effective pixels, never smaller than 1024 x 680, and reopens at its last size, position and maximised state.
- Dark only. Under a Windows contrast theme every custom colour gives way to the system colours and amber becomes the system highlight colour.
- The title bar is 48 high and drawn by the app (`ExtendsContentIntoTitleBar`), with a 1 px `raised` line under it. Left to right: the icon at 22, the wordmark `doubletake`, the tabs, a drag region, the Settings button (36 x 32, sliders glyph), then the system caption buttons.
- Tabs: `Scan`, `Review`, `History`. The current tab is `bodyStrong` in `text` with a 2 px `accent` line along the bottom edge, inset 14 px each side. Other tabs are `body` in `textMuted`. `Review` is disabled until a scan has produced at least one group.
- Settings is a fourth page reached by its button. While it shows, no tab is current and the button has a `raised` fill and an `accent` glyph.
- While a scan runs the Scan tab shows the Scanning page (section 5).
- The update notice (section 9.4) sits directly under the title bar on every page.

## 4. Scan

Mockup: `Scan.dc.html`. A 760 wide column, centred, starting 48 below the title bar, with 24 between blocks.

1. Title `Where are your photos?` in `pageTitle`.
2. Drop zone, 760 x 168: `panel` fill, 1.5 px dashed `strokeStrong` border, radius 10. Inside, centred: a folder glyph in `accent`, `Drop folders here` at 16, and a `Browse` button that opens the Windows folder picker with multiple selection. While folders are dragged over it the border becomes solid `accent` and the text reads `Drop to add`. Files dropped on it are ignored; only folders are added.
3. Folder chips, wrapping, 8 apart: each 36 high on `raised` with the path, the photo count in `caption` `textMuted`, and a remove button (28 x 28, named `Remove folder`). The count reads `counting` until the background count finishes.
4. Rules for the list: a folder already listed is not added twice. A folder inside a listed folder is not added, and a notice says `Already inside <parent>`. Adding a parent of listed folders replaces them. A folder that cannot be reached keeps its chip with `Not found` in place of the count and is left out of the scan. The list is remembered between runs.
5. Matching panel (`panel`, radius 10), two rows divided by a 1 px `raised` line:
   - `How close must a match be?` with a three-way choice `Exact`, `Close`, `Loose` (default `Close`). The chosen segment is `accent` with `onAccent` text. The caption follows the choice: `Exact`: `Only files that are byte for byte the same.` `Close`: `Close finds resized, recompressed and lightly edited copies.` `Loose`: `Loose also finds heavier edits and crops. Expect a few wrong matches to review.`
   - `Similar shots` with its caption and a switch, off by default. Turning it on when the model is absent opens the model dialog (section 9.3); if that is declined the switch returns to off.
6. `Start scan` (44 high, `accent`, 16 px 700) with the total beside it: `48,912 photos in 3 folders`. With no reachable folder the button is disabled and the text reads `Add a folder to start`.
7. Status bar, 36 high along the bottom, `caption` in `textMuted`: `Last scan 12 November 2026: 214 groups, 3.8 GB to recover`, or `No scan yet`.

## 5. Scanning

Mockup: `Scanning.dc.html`. The same 760 column, starting 72 below the title bar, 28 between blocks.

1. Title `Looking at your photos` while photos are read, then `Comparing` while groups are formed. Under it, the folder being read, on one line, ellipsised.
2. The count read so far in `bigNumber`, then `of 48,912 photos` at 16 in `textMuted`. Under them a 6 px progress bar: `raised` track, `accent` fill. During `Comparing` the bar is indeterminate and the count line reads `48,912 photos read`.
3. Three stat cards (`panel`, radius 10): `Duplicate groups so far` (value in `accent`), `Photos a second`, `Time so far`.
4. `Cancel scan` (36 high, secondary) with the note `Cancelling keeps what was read, so the next scan is faster.` Cancel acts at once, with no question, and returns to Scan with the status bar reading `Scan cancelled. 18,204 photos read.`
5. Status bar: `Reading 3 folders. 12,480 photos unchanged since the last scan were skipped.` When files could not be read it adds `14 files could not be read.` with an `Open log` link.
6. When the scan ends the Review tab opens with the notice `Scan finished. 214 groups found.` With no groups, Review shows its empty state (section 10).

## 6. Review

Mockup: `Review.dc.html`.

**Queue**, 248 wide on the left, with a 1 px `raised` line on its right:

- A header line in `caption`: `214 groups, largest first` and `11 done`.
- One row per group, 64 high, radius 8, ordered by space to recover, largest first: a pair of overlapping thumbnails (46 x 34, radius 4), `Group 12` in `bodyStrong`, and `3 resized, 7.9 MB` in `caption`. The current row has a `raised` fill and an 8 px `accent` dot. A decided row shows a tick in place of the dot and its text in `textMuted`.
- `Accept every suggestion` at the bottom (32 high, secondary, full width) decides every undecided group as suggested, after asking (section 9.7).

**Stage**, the rest of the width, padded 20 top and 24 at the sides:

- `Group 12 of 214` in `groupTitle`, then the kind, the count and the likeness: `Resized copy, 3 photos, 98% alike`. Kinds: `Exact copy`, `Resized copy`, `Recompressed copy`, `Edited copy`, `Similar shot`.
- Two panes side by side, 20 apart. Each has the photo (300 high, radius 10, fitted inside without cropping, on `panel`), a tag at its top left, the file name in `bodyStrong`, and four rows: `Resolution`, `File size`, `Taken`, `Folder`. Labels are `textMuted` and 96 wide.
- The left pane opens on the suggested keeper and the right on the next member. The keeper's photo has a 3 px `accent` outline and a `KEEP` tag (`accent` fill, `onAccent` text). The other tag reads `RECYCLE` (`ground` fill, `text`).
- Where the two differ in resolution or file size, the better value is `accent` and weight 600.
- The member strip under the panes lists every photo in the group at 96 x 72 with its tag. The two on show are outlined (the keeper in `accent`, the other in `text`). Choosing a member puts it in the right pane, or in the left pane when it is the keeper.

**Deciding a group.** A group starts undecided, showing the suggestion. Deciding marks every member KEEP or RECYCLE and moves to the next undecided group.

| Action | Key | Result |
| --- | --- | --- |
| Keep left | Left arrow | Left is KEEP, every other member RECYCLE |
| Keep right | Right arrow | Right is KEEP, every other member RECYCLE |
| Keep both | B | Both on show are KEEP, other members keep their suggestion |
| Skip | S | The group stays undecided and the next one opens |
| Undo | Ctrl+Z | The last decision is taken back and its group reopens |
| Previous or next group | Up, Down | Moves in the queue without deciding |
| Actual size | Z | Both panes switch between fitted and 100%, and pan together |
| Open the photo | Enter | Opens the focused pane's file in its default app |

- Clicking a tag switches that photo between KEEP and RECYCLE and decides the group. Switching a group's last KEEP is refused with the notice `Every group keeps at least one photo.`
- A pane's context menu: `Open`, `Show in folder`, `Copy path`.
- Decisions are saved as they are made, so closing the app loses none.

**Footer**, 56 high: key caps with their hints (`Left` keep left, `Right` keep right, `B` keep both, `Ctrl+Z` undo), then `27 photos marked, 412 MB`, then `Recycle marked` (36 high, `accent`), disabled when nothing is marked. It opens the dialog in section 9.1.

## 7. History

Mockup: `History.dc.html`. A 920 wide column, starting 40 below the title bar.

- Title `History` with the total on the right: `5.1 GB freed in 3 clean-ups`.
- One card per clean-up, newest first, 64 high when closed: the date and time, `327 photos moved to the Recycle Bin, 3.8 GB`, `3 folders scanned`, the state, `Restore` when it applies, and a chevron that opens the file list.
- States: `In Recycle Bin` (with `Restore`), `Restored 4 October`, `Partly restored`, `Recycle Bin emptied`. The state is checked against the Recycle Bin each time the page opens.
- The open card lists the first four files (path, size, `kept <file name>`) and `and 323 more`, which expands to the whole list in a box at most 320 high that scrolls.
- `Restore` puts back every photo of that clean-up still in the Recycle Bin, shows progress in the card, and ends with a notice: `327 photos put back.` or `301 photos put back. 26 were no longer in the Recycle Bin.`
- `Open Recycle Bin` opens the Windows Recycle Bin.

## 8. Settings and About

Mockup: `Settings.dc.html`. A 760 wide column of titled groups. Every setting takes effect at once and is saved.

| Group | Setting | Control | Default |
| --- | --- | --- | --- |
| Matching | Keep by default | List: `Highest resolution`, `Oldest photo`, `Newest photo` | `Highest resolution` |
| Matching | Similar shots | Switch, with the model state beside it | Off |
| Matching | Skip photos smaller than | List: `Do not skip`, `64 pixels`, `128 pixels`, `256 pixels` | `64 pixels` |
| Scanning | Include RAW files | Switch | On |
| Scanning | Scan hidden folders | Switch | Off |
| Updates | Tell me when a new version is out | Switch, with `Check now` | On |
| Your data | Scan index | Path and size, with `Clear index` | |
| Your data | Log files | `Open log folder` | |

- Model state reads `Model not downloaded`, `Downloading 40%`, `Ready` or `Download failed`.
- `Check now` answers with the update notice (section 9.4) or a notice `You have the newest version.` or `Could not check. Try again later.`
- `Clear index` asks first (section 9.5), is refused while a scan runs (`Wait for the scan to finish, or cancel it first.`), and ends with the notice `Index cleared.`
- About shows the icon at 56, `DoubleTake <version>`, the licence line, and four links: `Website`, `Source code`, `Licence`, `Third-party notices`. The first two open in the browser; the last two open the files installed with the app.

## 9. Dialogs and notices

Dialogs are 480 wide, `panel` with a 1 px `stroke` border and radius 10, over the `scrim` across the whole window. The footer is `ground` with two equal buttons 36 high: the action on the left in `accent`, `Cancel` on the right. Escape cancels. Notices are a 48 high `raised` bar across the top of the page with a glyph, the message, an optional action and a dismiss button.

1. **Recycle.** Mockup: `Dialogs.dc.html`. Title `Move 27 photos to the Recycle Bin?`, the explanation, then two rows: `Photos to recycle` (`27 in 11 groups`) and `Space freed once the bin is emptied` (`412 MB`, `accent`). Buttons `Move to Recycle Bin` and `Cancel`.
2. **Recycle result.** While files move, the dialog shows a progress bar and `Moving 12 of 27`, with `Stop` as its only button. Afterwards a notice: `27 photos moved to the Recycle Bin. 412 MB will be freed when you empty it.` with `Undo`, which restores that clean-up. A photo that changed or vanished since the scan is left alone and counted: `25 photos moved. 2 had changed since the scan and were left alone.`
3. **Model download.** Title `Download the similar shots model?`, body `<size> MB, one time. It runs on this PC and your photos stay here.` Buttons `Download` and `Not now`. While downloading: a progress bar, `Downloading 40%`, and `Cancel`. On failure: `The download did not finish. Check your connection and try again.` with `Try again` and `Close`.
4. **Update notice.** Mockup: `Dialogs.dc.html`. `DoubleTake 0.2.0 is out.` then `You have 0.1.0. The download page opens in your browser.`, the action `Get the new version` and a dismiss button. Dismissing hides the notice for that version for good. The app never downloads or installs an update.
5. **Clear index.** Title `Clear the scan index?`, body `The next scan will read every photo again. Your photos and History are not touched.` Buttons `Clear index` and `Cancel`.
6. **Problem notice.** The same bar with a warning glyph, for example `Could not read E:\Archive\2019. Check that the drive is connected.`
7. **Accept every suggestion.** Title `Accept every suggestion?`, body `214 groups will be decided as suggested. You can still change any of them.` Buttons `Accept` and `Cancel`.

## 10. Empty and edge states

| Where | When | What shows |
| --- | --- | --- |
| Scan | First run | The drop zone, no chips, `Add a folder to start`, status `No scan yet` |
| Review | Scan found nothing | Centred: `No duplicates found` in `pageTitle`, `48,912 photos, every one different.`, and `Scan again` |
| Review | Every group decided and recycled | Centred: `All done` in `pageTitle`, `327 photos moved to the Recycle Bin.`, and `Open History` |
| Review | A photo on show was moved or deleted outside the app | The pane shows `This photo is no longer there` and the group drops that member |
| History | No clean-up yet | Centred: `No clean-ups yet`, `Photos you recycle are listed here, ready to put back.` |
| Any page | The index cannot be opened | Problem notice with `Clear index`, and Scan stays usable |

## 11. Keyboard and accessibility

- Every control is reachable with Tab in reading order, shows a 2 px `accent` focus outline, and has a UI Automation name. Icon buttons are named for what they do (`Settings`, `Remove folder`, `Dismiss`, `Show files`).
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3` open Scan, Review and History. `Ctrl+,` opens Settings. `F5` on Scan starts the scan. `Esc` on Scanning cancels the scan.
- The Review keys in section 6 work whenever focus is in the stage or the queue, and never while a dialog is open.
- Each compare pane is announced with its file name, its tag and its four values. A decision is announced: `Kept left. Group 13 of 214.`
- Text contrast is at least 4.5 to 1. The layout holds at Windows text scaling from 100% to 200% and at the minimum window size, where the queue stays 248 wide and the panes shrink.

## 12. Text

- British spelling (`Minimise`, `Licence`), sentence case, no exclamation marks, no trailing full stop on buttons and labels.
- Counts use the user's Windows number format. Sizes use one decimal below 10 (`3.8 GB`, `0.6 MB`) and none from 10 up (`412 MB`). Dates and times use the user's Windows regional format.
- Every string lives in one resource file so wording changes in one place. This version ships in English only.

## 13. Brand assets

- **Icon.** On a 256 grid: a tile `x=16 y=16 w=224 h=224 rx=52` in `raised`; two rings of radius 56 centred at (104, 128) and (152, 128), stroke `text`; their overlap filled `accent` and drawn under the rings. Ring stroke is 10 at 48 px and larger, 14 at 32 and 24, and 20 at 16. Sources: [`brand/icon.svg`](brand/icon.svg) and [`brand/icon-small.svg`](brand/icon-small.svg).
- **Wordmark.** `doubletake` in Space Grotesk 700, lower case, tracking -0.04em, with `take` in `accent`. On a light ground, `double` is `ground` and `take` is `#8A5200`.
- **Tagline.** `Look twice. Keep one.`
- **Generated files.** One script builds every raster from the sources and `tokens.json`: the app icon (`.ico` with 16, 20, 24, 32, 40, 48, 64 and 256), the wordmark as outlines, the GitHub banner (1280 x 320), the GitHub social preview (1280 x 640), the share card (1200 x 630) and the Inno Setup wizard images. Mockups: `Brand.dc.html` and `Banners.dc.html`.

## 14. States to render

Each state below is captured from the running app into `build/renders/` and compared with its mockup by eye during review.

| Page | States |
| --- | --- |
| Scan | first run; three folders; drag over; a folder not found; each closeness choice; similar shots on |
| Scanning | reading; comparing; with unreadable files |
| Review | undecided group; decided group; group of three with the strip; actual size; nothing found; all done |
| History | none; one open in the bin; restored; partly restored; bin emptied |
| Settings | defaults; model downloading; model ready |
| Dialogs | recycle; recycle progress; model download in each state; clear index; update notice; problem notice |
| Window | minimum size; maximised; 200% text; contrast theme |

## 15. Not in this version

A light theme, languages other than English, video files, cloud libraries, in-app updating, scheduled scans, and moving duplicates to a folder instead of the Recycle Bin.
