---
schema_version: 1
id: similar-shots
domain: 04-ml
status: active
title: "TODO-01 -- Similar shots"
depends_on: ["history-settings"]
---

# TODO-01 -- Similar shots

> **Goal:** The optional Similar shots setting works: the user agrees to a one-time model download, the model is verified and runs on the PC, and a scan adds Similar groups (bursts, crops, heavier edits) after the duplicate groups, never mixed with them.

> **Current state:** Measured 2026-11-16. The setting and its two switches exist and return to off with an interim notice (`D03 T01 §3`, `D03 T03 §5`). `files.embedding` exists in the index and is empty. No ONNX Runtime package is referenced, no model is pinned and no dialog exists.

## Inputs

- `docs/plans/2026-11-16-doubletake-foundation.md` section 7 and decisions D5 and D8 (called "the foundation plan" below).
- `design/SPEC.md` sections 4 (item 5), 6 (kind `Similar shot`), 8 and 9.3.
- -> XREF: D03 T01 §3 -- the Scan page's Similar shots switch opens the dialog built in §5
- -> XREF: D03 T03 §5 -- the Settings page's switch and model state text are driven by §2 and §5
- -> XREF: D03 T02 §4 -- the Review queue lists the Similar groups built in §4 after the duplicate groups

## Outcome

- Turning Similar shots on downloads and verifies the model after the user agrees, and the setting stays on.
- A scan with it on adds Similar groups for the burst and crop fixtures, and none for the near-miss fixtures labelled different.

**Adjacency:** list=not-applicable (Similar groups join the Review queue, D03 T02 §4); document=not-applicable (nothing is carried or printed); settings=applicable @ D04 T01 §5; reporting=not-applicable (totals are reported by Review, D03 T02 §9); notifications=applicable @ D04 T01 §5; permissions=applicable @ D04 T01 §2; audit=not-applicable (downloads and failures go to the engine log, D01 T01 §1); exchange=not-applicable (the model is downloaded, never exported); reverse=applicable @ D04 T01 §5

**Adjacency rationale:** The switch is the setting and the scan is its consumer. The dialog tells the user about the download and its progress. A model that fails its checksum is refused and deleted in §2. Turning the switch off is the reverse: the model stays on disk but nothing runs, and `Remove model` in §5 deletes it.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | ONNX Runtime package and session wrapper | D03 T03 §11 | [ ] |
| 2 | §2 | Model pin and verified download | §1 | [ ] |
| 3 | §3 | Image preparation and embeddings | §2 | [ ] |
| 4 | §4 | Similar groups | §3 | [ ] |
| 5 | §5 | Model dialog and the two switches | §2, D03 T03 §5 | [ ] |
| 6 | §6 | Similar shots in scan and review | §4, §5 | [ ] |

## 1. ONNX Runtime package and session wrapper

**Phase:** 4
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Reference the package. Done when: the engine links it.
2. Add `src/engine/ml_session.cpp`. Done when: a tiny model runs.

- [ ] Add the `Microsoft.ML.OnnxRuntime.DirectML` NuGet package to the engine project with its version pinned, confirm its licence is MIT and record it and DirectML's licence in `NOTICE.md` (foundation plan D8, section 7). Done when: the engine builds and `onnxruntime.dll` and `DirectML.dll` are copied beside the executables. Cheaper substitute: building ONNX Runtime from source, which adds an hour to every clean build.
- [ ] Add `dt::MlSession` in `src/engine/ml_session.cpp`: open a model file with the DirectML provider, falling back to the CPU provider when DirectML cannot start, and report which is in use. Done when: `tests/engine/ml_session_tests.cpp` runs a 1 KB identity model committed under `tests/engine/data/` on both providers (the CPU one forced by an option). Cheaper substitute: failing on a machine with no DirectX 12 device.
- [ ] Return an `Error` for a missing file, a file that is not a model, and an input of the wrong shape, and never throw across the engine boundary. Done when: tests cover the three. Cheaper substitute: an uncaught ONNX Runtime exception ending the app.
- [ ] Load the runtime's DLLs only when a session is first opened, so an app with Similar shots off never loads them. Done when: a test of a scan with the setting off finds `onnxruntime.dll` absent from the process's module list. Cheaper substitute: paying the load time on every start.
- [ ] Commit: `engine: ONNX Runtime session wrapper`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[ml-session]"` passes, and fails when the CPU fallback is removed and DirectML is forced off.

## 2. Model pin and verified download

**Phase:** 4
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Pin the model. Done when: `resources/model.json` names a file that exists.
2. Add the download. Done when: a wrong checksum is refused.

- [ ] Confirm the model source: that the Hugging Face repository `onnx-community/dinov2-small` exists, serves an ONNX file of DINOv2 ViT-S/14, and is Apache-2.0; if any of the three does not hold, export the model with a committed script (`scripts/export-model.py`, from the official DINOv2 weights) and host the file as a GitHub release asset of this repository instead (foundation plan section 7). Done when: `docs/reviews/model-source.md` records the address, the licence text's location, the file size and the SHA-256, each checked on the day. Cheaper substitute: pinning an address from memory.
- [ ] Add `resources/model.json` (`name`, `url`, `bytes`, `sha256`, `input_size`, `embedding_size`, `licence`) and record the model in `NOTICE.md`. Done when: a test loads it and every field is present. Cheaper substitute: the address typed into the code.
- [ ] Add `dt::app::ModelStore` in `src/appcore/model_store.cpp`: `state()` (`NotDownloaded`, `Downloading`, `Ready`, `Failed`), and `download(cancel, progress)` streaming to `<data folder>\models\<name>.part` through `IHttp`, hashing as it writes. Done when: `tests/appcore/model_store_tests.cpp` downloads from the fake and ends `Ready`. Cheaper substitute: holding the whole model in memory.
- [ ] Verify size and SHA-256 before renaming `.part` to its final name; on a mismatch delete the file and end `Failed`. Done when: a test with one byte changed ends `Failed` with no file left. Cheaper substitute: loading a model that did not pass its check.
- [ ] Accept only `https`, starting at the host in `resources/model.json` and following a redirect only to a host in its `redirect_hosts` list, which is filled when the model is pinned by following the real download once and recording each host it passes through (a model hub serves files from separate storage hosts). Done when: a test with a fake redirecting to a listed host succeeds, one redirecting to an unlisted host is refused, and one real download of the pinned file, skipped with a clear line when offline, ends `Ready`. Cheaper substitute: refusing every redirect, which makes the real download impossible, or following any redirect.
- [ ] Resume nothing: a cancelled or failed download deletes its `.part` file, and `Ready` is decided at start by checking the final file's size and SHA-256 once, cached with its modified time. Done when: tests cover a cancelled download and a truncated final file found at start. Cheaper substitute: trusting a file because it exists.
- [ ] Add `remove()` deleting the model file. Done when: a test ends `NotDownloaded`. Cheaper substitute: none needed.
- [ ] Commit: `appcore: model pin and verified download`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only appcore -Filter "[model-store]"` passes, and fails when the SHA-256 check is skipped.

## 3. Image preparation and embeddings

**Phase:** 4
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/embed.cpp`. Done when: one photo gives one vector.
2. Batch and store. Done when: embeddings reach the index.

- [ ] Record the pinned model's own preprocessing in `resources/model.json` from its published preprocessor configuration: the shorter-side resize, the crop size, the resampling filter, the rescale factor and the mean and standard deviation. Done when: `docs/reviews/model-source.md` quotes the configuration file it was read from. Cheaper substitute: guessing the sizes, which quietly lowers the model's accuracy.
- [ ] Add `dt::prepare(image, config)` in `src/engine/embed.cpp` following that configuration exactly: resize the shorter side with the named filter, centre crop, convert BGRA to planar RGB floats, rescale and normalise. Done when: a test compares its output for two fixture photos with reference tensors made by the model's upstream preprocessing (a script, `scripts/make-reference-tensors.py`, and its outputs committed under `tests/engine/data/`), within a mean absolute difference of 0.02. Cheaper substitute: stretching to a square, or a filter of our own choosing.
- [ ] Add `dt::embed(session, images)` running batches of up to 16 and returning L2-normalised vectors of the model's embedding size. Done when: a test with the real model, skipped with a clear line when the model is not downloaded, gets vectors of length 1.0 within 1e-4. Cheaper substitute: unnormalised vectors, which make cosine similarity wrong.
- [ ] Store each vector in `files.embedding` as little-endian `float32`, with the model's name, so a model change invalidates old vectors. Done when: a test round-trips a vector and treats one stored under another model name as absent. Cheaper substitute: comparing vectors from two different models.
- [ ] Add an embedding stage to `dt::scan_and_group` at its extension point after duplicate groups are formed (`D01 T02 §5`), run only when the option is on and the model is `Ready`, only for photos in no duplicate group and with no current vector, with progress and cancel. Done when: a test sees no vector computed for a photo in a duplicate group, and a second scan computes none at all, checked by a counter. Cheaper substitute: embedding inside `dt::scan`, which runs before groups exist and so cannot leave grouped photos out.
- [ ] Commit: `engine: image preparation and embeddings`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[embed]"` passes, and fails when the centre crop is replaced by a stretch.

## 4. Similar groups

**Phase:** 4
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/similar.cpp`. Done when: close vectors pair up.
2. Set the limit from the fixtures. Done when: the test passes.

- [ ] Add `dt::find_similar(files, limit, cancel)` in `src/engine/similar.cpp`: cosine similarity by dot product over the normalised vectors, blocked so 50,000 photos finish in under a minute on the build machine. Done when: a timing test on random vectors passes and a brute-force check agrees on 2,000. Cheaper substitute: an approximate index, which adds a dependency before any measurement shows the need.
- [ ] Group the pairs at or above the limit with union-find into groups of kind `Similar`, leaving out any photo already in a hash group, with likeness as `round(100 x similarity)`. Done when: tests cover a burst of four, and a photo that is also a duplicate, which stays in its duplicate group only. Cheaper substitute: mixing Similar members into duplicate groups.
- [ ] Add burst and heavy-edit scenes to `tests/fixtures/make_fixtures.py` (the same scene with a moved subject, a 40% crop, a strong colour change) labelled `similar`, and keep the near-miss pairs labelled `different`. Done when: the manifest holds both labels. Cheaper substitute: tuning on the duplicate fixtures, which the hashes already find.
- [ ] Add `tests/engine/similar_accuracy_tests.cpp`, skipped with a clear line without the model: at the limit in foundation plan section 7 (0.90 to start), every `similar` pair is grouped and no `different` pair is; adjust the limit with the reason written beside it. Done when: the test passes with the model present. Cheaper substitute: loosening the test.
- [ ] Add the Similar stage to `dt::scan_and_group` after the embedding stage, and save Similar groups with `save_scan` after the duplicate groups, ordered by likeness, highest first. Done when: a test reads duplicate groups first, then Similar. Cheaper substitute: one list sorted by size, which mixes the two.
- [ ] Commit: `engine: similar groups`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[similar]"` passes, and fails when a photo in a duplicate group is also placed in a Similar group.

## 5. Model dialog and the two switches

**Phase:** 4
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 9.3, section 4 (item 5, second bullet) and section 8 (model state).
**Job:** the user agrees to a one-time download, sees it happen, and can stop it.
**Treatment:** a dialog stating the size and that photos stay on the PC, then a progress bar with Cancel, then a clear failure with Try again. Cheaper substitute that fails: downloading as soon as the switch is touched, with no word of the size.
**Chrome:** the `DtDialog` frame with a 6 px progress bar, and the two existing switches.

**Build order:**

1. Add the dialog. Done when: its three states show.
2. Replace the interim behaviour. Done when: the switches stay on after a download.

- [ ] Add `src/app/Dialogs/ModelDialog.xaml` with the ask state: `Download the similar shots model?`, `<size> MB, one time. It runs on this PC and your photos stay here.` with the size from `resources/model.json`, buttons `Download` and `Not now`. Done when: a UI test reads the texts and the real size. Cheaper substitute: a size typed into the string.
- [ ] Add the downloading state (progress bar, `Downloading <n>%`, `Cancel`) and the failed state (`The download did not finish. Check your connection and try again.`, `Try again`, `Close`), driven by `ModelStore`. Done when: UI tests with the fake `IHttp` reach each state. Cheaper substitute: a spinner with no percentage and no way out.
- [ ] Replace the interim notice of `D03 T01 §3` and `D03 T03 §5`: turning either switch on with the model `NotDownloaded` or `Failed` opens the dialog; the switch ends on only when the model is `Ready`, and returns to off on `Not now`, `Cancel` or `Close`. Done when: the UI tests of both pages are updated and pass, and the string `Similar shots arrive in a later version.` is removed from `resources/strings/en-GB.json`. Cheaper substitute: leaving the interim notice in place. -> XREF: D03 T01 §3
- [ ] Drive the Settings page's model state text (`Model not downloaded`, `Downloading 40%`, `Ready`, `Download failed`) from `ModelStore`, and add `Remove model` as a text button beside it when `Ready`, which turns the setting off and deletes the file after a dialog (`Remove the similar shots model?`, `You can download it again at any time.`). Done when: a UI test downloads, reads `Ready`, removes, and reads `Model not downloaded` with the switch off. Cheaper substitute: no way to get the disk space back. -> XREF: D03 T03 §5
- [ ] Add the remove control and its dialog to `design/SPEC.md` sections 8 and 9 and to `design/mockups/darkroom/Settings.dc.html` in the same commit, since the SPEC is the source of truth. Done when: the SPEC names `Remove model` and its dialog's text. Cheaper substitute: a control the SPEC does not know about.
- [ ] Capture `dialog-model-ask`, `dialog-model-downloading`, `dialog-model-failed`, `scan-similar-on`, `settings-model-downloading` and `settings-model-ready`, and set their `ready` flags in `tests/ui/capture-states.json`. Done when: the six PNGs exist and `scripts/capture-all.ps1` exits 0 with no state still waiting. Cheaper substitute: none needed.
- [ ] Commit: `app: model dialog and similar shots switches`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[model-dialog]"` passes, and fails when the switch stays on after `Not now`.

## 6. Similar shots in scan and review

**Phase:** 4
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 5 (phases), section 6 (kind `Similar shot`, queue order) and foundation plan section 7, last bullet.
**Job:** the user reviews look-alike shots after the true duplicates, knowing which is which.
**Treatment:** a third scan phase, and Similar groups at the end of the queue under their own heading with nothing suggested for recycling. Cheaper substitute that fails: listing look-alikes among duplicates with a recycle suggestion, which invites deleting different photos.
**Chrome:** the existing Scanning and Review pages, with one heading row in the queue.

**Build order:**

1. Add the scan phase. Done when: the Scanning page shows it.
2. Add the queue section. Done when: Similar groups are separate and unsuggested.

- [ ] Add the phase title `Finding similar shots` to `ScanningViewModel`, with a determinate bar over the photos to embed, between reading and comparing. Done when: a UI test with the setting on reads the title during a scan. Cheaper substitute: a long unexplained pause.
- [ ] Add a heading row `Similar shots` to the Review queue before the first Similar group, and number Similar groups after the duplicate groups. Done when: a UI test reads the heading between the last duplicate group and the first Similar one. Cheaper substitute: no boundary between the two.
- [ ] Suggest nothing for a Similar group: every member starts `SuggestKeep`, the panes show `KEEP` on both, and `Accept every suggestion` leaves Similar groups with nothing marked for recycling. Done when: a UI test accepts all and finds `marked_text` unchanged by the Similar groups. Cheaper substitute: recycling look-alikes the user never compared.
- [ ] Show `Similar shot, <n> photos, <likeness>% alike` in the stage summary, with the better resolution and file size marked exactly as for a duplicate pair. Done when: a UI test reads the summary of a burst group. Cheaper substitute: the wording of a duplicate.
- [ ] Add the two phrases to `design/SPEC.md` sections 5 and 6 (`Finding similar shots`, the `Similar shots` queue heading, and that nothing is suggested for recycling in a Similar group) in the same commit. Done when: the SPEC carries all three. Cheaper substitute: behaviour the SPEC does not describe.
- [ ] Capture `scanning-similar` and `review-similar-group`. Done when: both PNGs exist and `scripts/capture-all.ps1` lists them. Cheaper substitute: none needed.
- [ ] Commit: `app: similar shots in scan and review`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only ui -Filter "[similar-ui]"` passes, and fails when a Similar group has a member suggested for recycling.

## Verification

- On the build machine with a network connection: turning Similar shots on downloads and verifies the model; scanning the fixtures then lists the burst and crop scenes under `Similar shots`, with nothing marked for recycling, and none of the near-miss pairs.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
