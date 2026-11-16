---
schema_version: 1
id: match-and-clean
domain: 01-engine
status: active
title: "TODO-02 -- Match and clean up"
depends_on: ["scan-and-hash"]
---

# TODO-02 -- Match and clean up

> **Goal:** The engine turns hashed photos into groups of copies with a suggested keeper, stores the user's decisions, moves the unwanted copies to the Recycle Bin without ever deleting one outright, and can put a clean-up back.

> **Current state:** Measured 2026-11-16. `D01 T01` gives hashed `files` rows in the index and `doubletake-cli scan`. No matching, grouping, recycle or restore code exists, and the `groups`, `members`, `cleanups` and `cleanup_files` tables are empty.

## Inputs

- `docs/plans/2026-11-16-doubletake-foundation.md` sections 5.4, 5.5, 5.6 and 5.7 (called "the foundation plan" below).
- `dt::Index`, `dt::hamming` and the scan result from `D01 T01 §7` to `§9`.
- `build/fixtures/manifest.json` from `D00 T01 §7`.

## Outcome

- On the fixtures at Close, every pair labelled duplicate is in one group and no pair labelled different is.
- `doubletake-cli recycle` moves marked files to the Recycle Bin and `doubletake-cli restore` puts them back where they were.

**Adjacency:** list=not-applicable (the engine has no surface; the queue is drawn by D03 T02 §4); document=not-applicable (nothing is carried or printed); settings=applicable @ D01 T02 §4; reporting=applicable @ D01 T02 §10; notifications=not-applicable (results are returned to the caller, which owns what is shown); permissions=applicable @ D01 T02 §7; audit=applicable @ D01 T02 §8; exchange=not-applicable (decisions stay in the private index); reverse=applicable @ D01 T02 §9

**Adjacency rationale:** The keeper rule is the engine's one matching setting. The refusals are the rule that every group keeps a photo and the skip of a file that changed, both enforced in §4 and §7. Each clean-up is recorded file by file in §8, which is the audit trail and what restore in §9 reads. The console commands in §10 report over groups and clean-ups.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | BK-tree over 64-bit hashes | D01 T01 §7 | [ ] |
| 2 | §2 | Pair matching by closeness | §1, D01 T01 §9 | [ ] |
| 3 | §3 | Groups, kinds and likeness | §2 | [ ] |
| 4 | §4 | Keeper suggestion and marks | §3 | [ ] |
| 5 | §5 | Group storage and decisions in the index | §4, D01 T01 §8 | [ ] |
| 6 | §6 | Fixture accuracy test | §5 | [ ] |
| 7 | §7 | Recycle through the Windows shell | §5 | [ ] |
| 8 | §8 | Clean-up records | §7 | [ ] |
| 9 | §9 | Restore from the Recycle Bin | §8 | [ ] |
| 10 | §10 | Console program: groups, recycle and restore | §6, §9 | [ ] |

## 1. BK-tree over 64-bit hashes

Near matches without comparing every photo to every other.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/bktree.h`. Done when: a range query returns the right set.
2. Prove it against brute force. Done when: the two agree on random data.

- [ ] Add `dt::BkTree` in `src/engine/bktree.h` with `insert(hash, id)` and `query(hash, maxDistance, out)` over Hamming distance, stored in flat vectors (foundation plan section 5.4). Done when: `tests/engine/bktree_tests.cpp` finds exact, near and no matches in a hand-built set. Cheaper substitute: comparing all pairs, which takes hours on a large library.
- [ ] Keep every id for a repeated hash. Done when: a test inserting one hash three times gets three ids back at distance 0. Cheaper substitute: dropping duplicates of a hash, which loses exact visual copies.
- [ ] Compare against brute force on 5,000 random hashes with 200 planted neighbours at limits 0, 6 and 12. Done when: both give the same sets. Cheaper substitute: testing only hand-picked values.
- [ ] Commit: `engine: BK-tree`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[bktree]"` passes, and fails when the child range in `query` is narrowed by one.

## 2. Pair matching by closeness

Which two photos count as copies at each of the three settings.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/match.cpp`. Done when: it returns confirmed pairs.
2. Cover each closeness. Done when: the table in the foundation plan is tested row by row.

- [ ] Add `dt::Closeness` (`Exact`, `Close`, `Loose`) and `dt::Limits` holding the pHash limit, dHash limit and aspect rule for each, in one table in `src/engine/match.cpp` with the starting values of foundation plan section 5.4. Done when: a test reads the three rows. Cheaper substitute: limits scattered as literals through the code.
- [ ] Add `dt::find_pairs(files, closeness, cancel)`: files with equal BLAKE3 are exact pairs; at `Close` and `Loose`, candidates from the BK-tree on pHash are confirmed by the dHash limit and, at `Close`, by aspect ratios within 2%. Done when: tests cover a pair that passes pHash but fails dHash, and one that fails only the aspect rule. Cheaper substitute: pHash alone, which lets unrelated low-detail photos pair.
- [ ] At `Exact` return exact pairs only and build no tree. Done when: a test at `Exact` on a resized fixture returns no pair. Cheaper substitute: pHash distance 0 as "exact", which is not byte for byte.
- [ ] Return each pair once, with its pHash distance. Done when: a test of three mutual copies returns three pairs, not six. Cheaper substitute: both orders, doubling later work.
- [ ] Commit: `engine: pair matching by closeness`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[match]"` passes, and fails when the dHash confirmation is removed.

## 3. Groups, kinds and likeness

From pairs to the groups the user reviews.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/group.cpp`. Done when: pairs become groups.
2. Classify. Done when: each kind is tested.

- [ ] Add `dt::build_groups(pairs)` with union-find, giving each group its members in a stable order (by path). Done when: tests cover two separate groups, a chain of three, and files in no pair, which form no group. Cheaper substitute: groups whose order changes between runs.
- [ ] Add `dt::kind_of(a, b)`: `Exact` for equal BLAKE3, `Recompressed` for equal pixel size and different bytes, `Resized` for different pixel size with aspect within 2%, else `Edited` (foundation plan section 5.4). Done when: a test covers each kind with fixture variants. Cheaper substitute: one kind, "duplicate", which hides why two files matched.
- [ ] Add `dt::likeness(a, b)` as `round(100 x (64 - distance) / 64)`, and 100 for an exact pair. Done when: tests cover distance 0, 1 and 64. Cheaper substitute: a made-up confidence figure.
- [ ] Add `dt::recoverable_bytes(group, keeper)` as the sum of every member's size but the keeper's. Done when: a test of three files gives the two smaller sizes summed when the largest is kept. Cheaper substitute: the group's total size.
- [ ] Commit: `engine: groups, kinds and likeness`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[group]"` passes, and fails when `kind_of` treats a different pixel size as `Recompressed`.

## 4. Keeper suggestion and marks

Which copy the app proposes to keep, and the rule that a group never loses its last photo.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/keeper.cpp`. Done when: each rule picks the right file.
2. Add marks. Done when: the last-keeper rule is enforced.

- [ ] Add `dt::KeepRule` (`HighestResolution`, `Oldest`, `Newest`) and `dt::suggest_keeper(group, rule)` with the tie order of foundation plan section 5.5: pixel count, file size, capture date, path length, path. Done when: tests give each rule a group where it alone decides, and a full tie decided by path. Cheaper substitute: the first file found, which changes with scan order.
- [ ] Treat a missing capture date as unknown: it loses to any known date under `Oldest` and `Newest`. Done when: a test with one dated and one undated file keeps the dated one under both rules. Cheaper substitute: treating unknown as the epoch, which makes undated files the "oldest".
- [ ] Add `dt::Mark` (`SuggestKeep`, `SuggestRecycle`, `Keep`, `Recycle`) and `dt::Decision` functions: `keep_only(group, member)`, `keep_both(group, a, b)`, `toggle(group, member)` and `accept_suggestion(group)`. Done when: tests cover each on a group of three. Cheaper substitute: a boolean per file, which cannot tell a suggestion from a decision.
- [ ] Refuse any change that would leave a group with no `Keep` or `SuggestKeep` member, returning a distinct `Error`. Done when: toggling a group's only keeper to recycle is refused and the marks are unchanged. Cheaper substitute: enforcing the rule only in the interface (`design/SPEC.md` section 6).
- [ ] Commit: `engine: keeper suggestion and marks`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[keeper]"` passes, and fails when the last-keeper refusal is removed.

## 5. Group storage and decisions in the index

Groups and decisions survive closing the app.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add group writes and reads to `src/engine/index.cpp`. Done when: groups round-trip.
2. Add decisions and undo. Done when: both persist.

- [ ] Add `save_scan(scan, groups)` writing a `scans` row and its `groups` and `members` in one transaction, replacing the groups of any earlier scan, ordered by bytes to recover, largest first. Done when: a test saves, reopens the database and reads the same groups in the same order. Cheaper substitute: keeping groups only in memory.
- [ ] Add `load_groups(scan)` and `load_group(id)` joining members to their file rows. Done when: a group reads back with every member's path, sizes, date and mark. Cheaper substitute: one query per member.
- [ ] Add `set_marks(group, marks)` writing the marks and the `decided` flag in one transaction, and an `undo_log` table holding the previous marks of the last 100 decisions of the scan. Done when: a test decides three groups, undoes twice, reopens the database and finds the first decision only. Cheaper substitute: an undo stack in memory, lost on close.
- [ ] Add `marked_totals(scan)` returning the count and bytes of `Recycle` marks in decided groups. Done when: a test matches a hand count. Cheaper substitute: counting suggestions too, which overstates what will be recycled.
- [ ] Add `latest_scan()` returning the newest finished scan with its summary. Done when: a test with two scans returns the second. Cheaper substitute: none needed.
- [ ] Add `dt::scan_and_group(options, closeness, rule, index, cancel, progress)` in `src/engine/pipeline.cpp`, the one owner of the whole sequence: read and hash (`dt::scan`), find pairs, build groups, suggest keepers, `save_scan`. It reports its stage in the progress value, and has a named extension point after duplicate groups are formed for the stages `D04 T01 §3` and `§4` add. Done when: a test runs it on the fixtures and reads saved groups, and a cancel during any stage leaves no half-saved scan. Cheaper substitute: each caller (the console program, the app) stitching the stages together its own way.
- [ ] Commit: `engine: group storage and decisions`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[groups-store]"` passes, and fails when `set_marks` does not write the undo row.

## 6. Fixture accuracy test

The test that owns the matching limits.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `tests/engine/accuracy_tests.cpp`. Done when: it scores the manifest.
2. Settle the limits. Done when: Close is perfect on the fixtures.

- [ ] Add `tests/engine/accuracy_tests.cpp`: scan `build/fixtures/`, match at each closeness, and compare every labelled pair in the manifest with the groups. Done when: it prints found, missed and wrong pairs per closeness. Cheaper substitute: checking a handful of pairs by name.
- [ ] Require at `Close`: every pair labelled duplicate (other than crops) in one group, and no pair labelled different grouped. Done when: the test passes, with the limits in `dt::Limits` adjusted if needed and the reason for any change written beside the table. Cheaper substitute: loosening the test instead of fixing the limits.
- [ ] Require at `Exact`: only the byte-identical copies grouped. Done when: the test passes. Cheaper substitute: none needed.
- [ ] Require at `Loose`: every crop grouped with its scene, and record how many near-miss pairs are grouped as the known cost. Done when: the test passes and the count is asserted so a regression shows. Cheaper substitute: an unbounded number of wrong matches.
- [ ] Assert each duplicate pair's kind matches the manifest. Done when: the test passes for every kind. Cheaper substitute: none needed.
- [ ] Commit: `tests: fixture accuracy for every closeness`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[accuracy]"` passes, and fails when the `Close` pHash limit is raised to 20.

## 7. Recycle through the Windows shell

The one place a user's file is moved, and the checks before it.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/recycle.cpp`. Done when: a file reaches the Recycle Bin.
2. Add the guards. Done when: each skip is tested.

- [ ] Add `dt::recycle(files, cancel, progress)` in `src/engine/recycle.cpp` using `IFileOperation` with `FOFX_RECYCLEONDELETE`, `FOF_NOCONFIRMATION`, `FOF_NOERRORUI` and `FOF_SILENT`, one file per operation so each result is known (foundation plan section 5.7). Done when: a test recycles a file in a temporary folder and finds it gone from the folder and present in the Recycle Bin. Cheaper substitute: `DeleteFile`, which destroys the photo.
- [ ] Make permanent deletion impossible through an `IFileOperationProgressSink`: in `PreDeleteItem`, fail the item unless its flags carry `TSF_DELETE_RECYCLE_IF_POSSIBLE`, which the shell clears when the item would be deleted outright (recycling turned off for the drive, a file too large for the bin, a volume with no bin); in `PostDeleteItem`, treat an item with no newly created bin item as not recycled. Read both members' documentation on Microsoft Learn on the day and cite it in a comment. Done when: a test with a sink seam reporting the flag clear leaves the file in place and counts it skipped, and a test on a disposable VHD or drive with recycling disabled, skipped with a clear line when none can be made, leaves the file in place. Cheaper substitute: `SHQueryRecycleBin`, which reports a bin's totals and says nothing about whether one file can be recycled.
- [ ] Return for each recycled file the bin item's identity: the parsing name of the item `PostDeleteItem` hands back (`SIGDN_DESKTOPABSOLUTEPARSING`), with the deletion time. Done when: a test reads an identity for each of three recycled files and each names an existing item under the Recycle Bin. Cheaper substitute: remembering only the original path, which is not unique once the same path is recycled twice.
- [ ] Before each file, compare its size and modified time with the index row; skip and count a file that differs or is gone. Done when: tests cover an edited file and a deleted file, and neither is touched. Cheaper substitute: recycling whatever is at the path now.
- [ ] Refuse the whole call when the file list would empty a group: every group named must keep at least one member that is not in the list. Done when: a test passing all members of a group is refused and nothing moves. Cheaper substitute: trusting the caller.
- [ ] Before moving any file of a group, check that at least one member being kept still exists on disk with the size and modified time the index holds; when none does, leave the whole group untouched and count it. Done when: a test deletes a group's keeper outside the engine, recycles, and finds the group's other members still in place. Cheaper substitute: checking only that a keeper is marked, which recycles the last surviving copy when the keeper has gone.
- [ ] Report progress per file and stop between files on cancel, returning what was moved. Done when: a test cancels after two of five and finds exactly two moved. Cheaper substitute: an all-or-nothing call the user cannot stop.
- [ ] Clean up after the tests: every file a test recycles is restored or purged from the bin by the test itself. Done when: the Recycle Bin item count is the same before and after the test program. Cheaper substitute: leaving test files in the user's bin.
- [ ] Commit: `engine: recycle through the Windows shell`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[recycle]"` passes, and fails when the changed-file check is removed.

## 8. Clean-up records

What was moved, written as it happens.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add clean-up writes to `src/engine/index.cpp`. Done when: a clean-up is recorded.
2. Join it to recycle. Done when: a crash loses no record.

- [ ] Add `begin_cleanup(scan)`, `add_pending_file(cleanup, path, size, keptPath)`, `confirm_file(cleanup, path, binIdentity, deletedAt)`, `drop_pending_file(cleanup, path)` and `finish_cleanup(cleanup)` for the `cleanups` and `cleanup_files` tables, with a `state` column on each file (`pending`, `recycled`). Done when: a test reads back a clean-up with its files and their states. Cheaper substitute: one write at the end, lost if the app dies midway.
- [ ] Add `dt::clean_up(scan, index, cancel, progress)`: take the `Recycle` members of decided groups and, for each, commit its `pending` row before the shell moves it, then `confirm_file` with the bin identity after, or `drop_pending_file` when it was skipped. Done when: a test that stops after two files finds a clean-up with two `recycled` files. Cheaper substitute: writing the record only after the move, which loses a file's record when the app dies between the two.
- [ ] Add `dt::reconcile_cleanups(index)`, run when the index opens: for each `pending` row, the file still at its path means the move never happened, so drop the row; the file gone means it moved, so find its bin item by original path, requiring exactly one candidate deleted after the row was written, and confirm it, or mark it `recycled` with no identity when none or several match. Done when: a test that ends the process between the pending write and the confirm (through a fault hook), then reopens the index, finds the row confirmed with an identity. Cheaper substitute: leaving `pending` rows for ever, so History cannot restore those files.
- [ ] Remove recycled members from their groups, and remove a group left with one member. Done when: after a clean-up, `load_groups` returns only groups still holding copies. Cheaper substitute: leaving dead groups in the queue.
- [ ] Add `list_cleanups()` newest first with photo count, bytes and folder count, and `cleanup_files(cleanup, offset, limit)`. Done when: tests cover paging. Cheaper substitute: none needed.
- [ ] Write one log line per clean-up with its counts and one per skipped file with the reason (foundation plan section 5.8). Done when: a test finds them in the log. Cheaper substitute: none needed.
- [ ] Commit: `engine: clean-up records`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[cleanup]"` passes, and fails when records are written only at the end.

## 9. Restore from the Recycle Bin

The undo of a clean-up.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/restore.cpp`. Done when: a recycled file returns to its folder.
2. Add states. Done when: each state is read from the bin.

- [ ] Add `dt::RecycleBin::find(binIdentity)` in `src/engine/restore.cpp`, binding the stored parsing name to its Recycle Bin item and checking the item's original location equals the recorded path (foundation plan section 5.7). Done when: a test recycles the same path twice with different bytes and `find` returns the right item for each identity. Cheaper substitute: matching by original path and a time window, which picks the wrong item when one path was recycled twice.
- [ ] For a file recorded with no identity (reconciled after a crash), fall back to the original location and deletion time and restore only when exactly one bin item matches; count it as not restorable otherwise. Done when: a test with two candidates restores neither and reports one ambiguous file. Cheaper substitute: restoring the first candidate.
- [ ] Add `dt::restore(cleanup, index, cancel, progress)` invoking the shell's own restore verb on each found item, marking `cleanup_files.restored`, and counting files no longer in the bin. Done when: a test restores three recycled files to their original paths with their original bytes. Cheaper substitute: copying files out of `$Recycle.Bin` by hand, which skips the shell's bookkeeping.
- [ ] Never overwrite: when a file already exists at the original path, leave the bin item alone and count it. Done when: a test with a new file at the path leaves both untouched. Cheaper substitute: replacing whatever is there.
- [ ] Add `cleanup_state(cleanup)` returning `InBin`, `Restored`, `PartlyRestored` or `BinEmptied` from the restored flags and what the bin holds now. Done when: tests cover the four. Cheaper substitute: a state stored once and never checked against the bin.
- [ ] Commit: `engine: restore from the Recycle Bin`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[restore]"` passes, and fails when the overwrite guard is removed.

## 10. Console program: groups, recycle and restore

The whole engine, end to end, from a command line.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add the commands to `src/cli/`. Done when: each runs against a data folder.
2. Test the round trip. Done when: files leave and come back.

- [ ] Add `doubletake-cli groups --data-dir <dir> [--closeness exact|close|loose] [--keep resolution|oldest|newest] [--json]` matching the latest scan through `dt::scan_and_group`'s grouping stages and printing each group with its kind, likeness and members, the suggested keeper first. Done when: on the fixtures it prints one group per scene. Cheaper substitute: none needed.
- [ ] Hold `accept`, `recycle` and `restore` to the required `--data-dir` rule of `D01 T01 §10`, and make `recycle` refuse any file outside the folders that data folder's scan covered. Done when: a test running `recycle` with no `--data-dir` reads exit 2 and moves nothing. Cheaper substitute: commands that act on whatever index the machine's owner has.
- [ ] Add `doubletake-cli accept` (decide every group as suggested), `recycle` (run the clean-up, printing moved and skipped counts) and `restore [<cleanup-id>]` (the latest by default). Done when: each exits 0 on a copy of the fixtures. Cheaper substitute: none needed.
- [ ] Add `tests/engine/cli_roundtrip_tests.cpp`: copy the fixtures to a temporary folder, run `scan`, `groups`, `accept`, `recycle`, check only keepers remain, run `restore`, and check every file is back with its original BLAKE3. Done when: the test passes and leaves the Recycle Bin as it found it. Cheaper substitute: asserting only exit codes.
- [ ] Give the test the process rules of `D01 T01 §10`: a time limit, the whole process tree ended on timeout, no console window. Done when: a hung child is ended and reported. Cheaper substitute: an orphaned process after a failed run.
- [ ] Commit: `cli: groups, recycle and restore commands`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[cli-roundtrip]"` passes, and fails when `restore` skips marking files restored.

## Verification

- On a copy of the fixtures in a temporary folder, `doubletake-cli scan`, `groups`, `accept`, `recycle` and `restore`, each run with the same fresh `--data-dir` under `build/`, leave every file where it started, the Recycle Bin as it was, and `%LOCALAPPDATA%\DoubleTake` unchanged; and the accuracy test passes at all three settings.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
