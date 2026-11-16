---
schema_version: 1
id: scan-and-hash
domain: 01-engine
status: active
title: "TODO-01 -- Scan and hash"
depends_on: ["repo-and-build"]
---

# TODO-01 -- Scan and hash

> **Goal:** The engine walks folders, decodes every supported photo format with its orientation applied, computes the exact and perceptual hashes, and keeps them in an index so an unchanged photo is never read twice. A console program runs a scan end to end.

> **Current state:** Measured 2026-11-16. `D00 T01 §3` gives an engine library with only `dt::version()`. `D00 T01 §7` and `§8` give `build/fixtures/` with a labelled manifest. No scan, decode, hash or index code exists.

## Inputs

- `docs/plans/2026-11-16-doubletake-foundation.md` sections 5.1, 5.2, 5.3, 5.6 and 5.8 (called "the foundation plan" below).
- `build/fixtures/manifest.json` from `D00 T01 §7`.
- vcpkg ports `blake3`, `sqlite3`, `libheif`, `libraw` from `D00 T01 §2`.

## Outcome

- `doubletake-cli scan <folder>` reads a folder of mixed formats and prints one line per photo with its size, pixel size and three hashes.
- A second scan of the same folder reads no file again.

**Adjacency:** list=not-applicable (the engine has no surface; lists are drawn by D03 T02 §4); document=not-applicable (nothing is carried or printed); settings=applicable @ D01 T01 §9; reporting=applicable @ D01 T01 §10; notifications=not-applicable (progress is published to the caller, which owns what is shown); permissions=applicable @ D01 T01 §2; audit=applicable @ D01 T01 §1; exchange=not-applicable (the index is private to the app); reverse=not-applicable (a scan changes no user file)

**Adjacency rationale:** The scan options (hidden folders, RAW, minimum size) are the engine's settings and are consumed by the pipeline in §9. Folders and files that cannot be read are the refusals, recorded in §2 and §9. The log in §1 is the diagnostic trail. The console program in §10 is the report over a scan.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Cancel token, result type and log | D00 T01 §4 | [ ] |
| 2 | §2 | Folder walk and photo format table | §1 | [ ] |
| 3 | §3 | WIC decoder with orientation and metadata | §1, D00 T01 §7 | [ ] |
| 4 | §4 | libheif decoder | §3, D00 T01 §8 | [ ] |
| 5 | §5 | LibRaw decoder | §3, D00 T01 §8 | [ ] |
| 6 | §6 | BLAKE3 exact hash | §1 | [ ] |
| 7 | §7 | dHash and pHash | §3 | [ ] |
| 8 | §8 | Index database and migrations | §1 | [ ] |
| 9 | §9 | Scan pipeline with progress and cancel | §2, §4, §5, §6, §7, §8 | [ ] |
| 10 | §10 | Console program: scan | §9 | [ ] |

## 1. Cancel token, result type and log

The three things every engine function uses: a way to stop, a way to fail without throwing across the library boundary, and a place to write what happened.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `include/doubletake/core.h`. Done when: `CancelToken`, `Result<T>` and `Error` compile and are tested.
2. Add `src/engine/log.cpp`. Done when: the log rotates.

- [ ] Add `dt::CancelToken` (a shared atomic flag with `cancel()` and `cancelled()`) and `dt::Error` (a code from one `enum class ErrorCode` and a UTF-8 message) with `dt::Result<T>` holding a value or an `Error`, in `include/doubletake/core.h` (foundation plan section 5). Done when: `tests/engine/core_tests.cpp` covers a value, an error and a cancelled token seen from another thread. Cheaper substitute: exceptions thrown through the public interface.
- [ ] Add `dt::Log` in `src/engine/log.cpp` writing UTF-8 lines with a UTC timestamp and level to a file, rotating at 1 MB and keeping five files (foundation plan section 5.8). Done when: a test writing 6 MB leaves exactly five files, none over 1 MB plus one line. Cheaper substitute: an unbounded log, which can fill a disk.
- [ ] Make `dt::Log` safe from many threads. Done when: a test with eight threads writing 1,000 lines each finds 8,000 whole lines. Cheaper substitute: interleaved half lines.
- [ ] Commit: `engine: cancel token, result type and log`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[core]"` passes, and fails when rotation is removed from `dt::Log`.

## 2. Folder walk and photo format table

Finding the photos, and skipping what must not be followed.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/formats.cpp`. Done when: an extension maps to a decoder family.
2. Add `src/engine/walk.cpp`. Done when: it lists photos and records unreadable folders.

- [ ] Add the format table in `src/engine/formats.cpp`: each extension in foundation plan section 5.2, matched without case, with its decoder family (`Wic`, `Heif`, `Raw`). Done when: `tests/engine/formats_tests.cpp` covers every extension and rejects `.txt` and a name with no extension. Cheaper substitute: sniffing every file's first bytes, which reads the whole disk.
- [ ] Add `dt::walk(folder, options, cancel, sink)` in `src/engine/walk.cpp` yielding path, size and modified time for each photo, skipping reparse points, and skipping hidden and system folders unless `options.hidden` (foundation plan section 5.1). Done when: a test tree with a junction, a hidden folder and nested folders yields exactly the expected files, both ways for `hidden`. Cheaper substitute: following junctions, which loops on a folder that links to its parent.
- [ ] Record a folder that cannot be opened as an `Error` to the sink and keep walking. Done when: a test with a folder whose access is denied sees the error and still gets the files beside it. Cheaper substitute: aborting the whole walk on the first denied folder.
- [ ] Leave RAW extensions out when `options.raw` is false. Done when: a test with a `.dng` beside a `.jpg` yields one file. Cheaper substitute: decoding them and discarding the result.
- [ ] Use long-path aware APIs so a path over 260 characters is walked. Done when: a test creating a 300 character path finds its file. Cheaper substitute: silently skipping long paths.
- [ ] Commit: `engine: folder walk and format table`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[walk]"` passes, and fails when the reparse point check is removed.

## 3. WIC decoder with orientation and metadata

The common formats, through the decoder Windows already has.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `include/doubletake/decode.h` and `src/engine/decode_wic.cpp`. Done when: a JPEG decodes to BGRA at a requested size.
2. Apply orientation and read metadata. Done when: the rotated fixture matches its original.

- [ ] Add `dt::Image` (width, height, 8-bit BGRA pixels) and `dt::PhotoInfo` (pixel width and height of the full image, capture date, camera model) with `dt::decode(path, longestSide, cancel)` returning both, in `include/doubletake/decode.h` (foundation plan section 5.2). Done when: the header compiles in the test program. Cheaper substitute: returning a WIC interface, which ties callers to COM.
- [ ] Implement the `Wic` family in `src/engine/decode_wic.cpp` with `IWICImagingFactory`, scaling with the Fant interpolation mode to the requested longest side and converting to 32bpp BGRA. Done when: a test decodes a fixture JPEG, PNG, BMP, GIF and TIFF at longest side 256 and gets the right dimensions. Cheaper substitute: decoding at full size and shrinking by skipping pixels.
- [ ] Apply the EXIF orientation (values 1 to 8) so the returned pixels are upright, and report the upright full-image size. Done when: the fixture stored rotated with an orientation tag decodes to pixels within a mean difference of 2 levels of its original. Cheaper substitute: ignoring orientation, which makes a rotated copy look different.
- [ ] Read `DateTimeOriginal` and the camera model through the WIC metadata query reader, leaving them empty when absent. Done when: a test reads the date written by the fixture generator and gets empty for a PNG. Cheaper substitute: using the file's modified time as the capture date.
- [ ] Return an `Error` with a distinct code for a missing file, an unsupported or damaged file, and a missing WIC codec (WebP on an older Windows). Done when: tests cover a truncated JPEG and a text file renamed `.jpg`. Cheaper substitute: returning an empty image as success.
- [ ] Commit: `engine: WIC decoder with orientation and metadata`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[decode-wic]"` passes, and fails when the orientation step is removed.

## 4. libheif decoder

Phone photos.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/decode_heif.cpp`. Done when: the HEIC sample decodes.
2. Match the WIC contract. Done when: orientation and metadata behave the same.

- [ ] Implement the `Heif` family in `src/engine/decode_heif.cpp` with libheif: decode the primary image to interleaved RGB, convert to BGRA and scale to the requested longest side by area averaging. Done when: `tests/fixtures/samples/scene01.heic` decodes to within a mean difference of 6 levels of its scene's original. Cheaper substitute: asking Windows for the HEIC codec, which many machines lack.
- [ ] Let libheif apply the image's own transformations (`irot`, `imir`) and do not apply the EXIF orientation again. Done when: a test with a rotated HEIC, made in the fixture step, decodes upright once. Cheaper substitute: applying both, which turns the photo twice.
- [ ] Read the capture date and camera model from the EXIF block libheif exposes. Done when: a test reads them from the sample. Cheaper substitute: leaving HEIC photos without dates, which breaks the oldest and newest keeper rules for phones.
- [ ] Record in `NOTICE.md` the licences of libheif and of the decoder plugins the vcpkg build actually links (foundation plan D8). Done when: the list matches `vcpkg list`. Cheaper substitute: none needed.
- [ ] Commit: `engine: libheif decoder`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[decode-heif]"` passes, and fails when the decoder returns the image without scaling.

## 5. LibRaw decoder

Camera RAW files, read through their embedded preview when it is good enough.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/decode_raw.cpp`. Done when: both DNG samples decode.
2. Prefer the preview. Done when: the choice is tested.

- [ ] Implement the `Raw` family in `src/engine/decode_raw.cpp` with LibRaw: use the embedded JPEG preview when it is at least 1024 wide, decoding it through the `Wic` path from memory (foundation plan section 5.2). Done when: the sample with a preview decodes without LibRaw's full processing being called (checked by a counter in the test build). Cheaper substitute: a full demosaic of every RAW file, which is many times slower.
- [ ] Otherwise decode with `half_size`, camera white balance and sRGB output. Done when: the sample with no preview decodes to within a mean difference of 10 levels of its scene. Cheaper substitute: failing on RAW files with no preview.
- [ ] Apply the orientation LibRaw reports (`sizes.flip`) and read the capture date and camera model. Done when: tests read them from a sample. Cheaper substitute: none needed.
- [ ] Bound memory: refuse, with an `Error`, a file whose declared raw size is over 200 megapixels. Done when: a test with a crafted header is refused without a large allocation. Cheaper substitute: trusting the header's dimensions.
- [ ] Commit: `engine: LibRaw decoder`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[decode-raw]"` passes, and fails when the preview path is disabled.

## 6. BLAKE3 exact hash

Byte-identical files, found without decoding anything.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/exact_hash.cpp`. Done when: it matches the reference vectors.
2. Stream large files. Done when: memory stays flat.

- [ ] Add `dt::blake3_file(path, cancel)` returning 32 bytes, reading in 1 MB blocks, in `src/engine/exact_hash.cpp` (foundation plan section 5.3). Done when: `tests/engine/exact_hash_tests.cpp` matches BLAKE3's published test vectors for the empty input and for 1,024 bytes of the standard pattern. Cheaper substitute: hashing only the first megabyte, which calls different files identical.
- [ ] Stop within one block when the token is cancelled, returning a cancelled `Error`. Done when: a test cancelling during a 64 MB file returns in under a second. Cheaper substitute: finishing the file first.
- [ ] Return an `Error` for a file that cannot be opened or shrinks while read. Done when: tests cover a missing file and a locked file. Cheaper substitute: returning a hash of the bytes that were read.
- [ ] Commit: `engine: BLAKE3 exact hash`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[exact]"` passes, and fails when the block loop stops after the first block.

## 7. dHash and pHash

The two perceptual hashes, written here so they give the same bits on every machine.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/perceptual.cpp`. Done when: both hashes compute from a `dt::Image`.
2. Pin their values. Done when: golden values are tested.

- [ ] Add grey conversion (Rec. 601 luma) and area-average reduction to a requested size in `src/engine/perceptual.cpp` (foundation plan section 5.3). Done when: a test reduces a two-colour checker to its exact mean. Cheaper substitute: nearest-neighbour sampling, which makes the hash jump with tiny shifts.
- [ ] Add `dt::dhash(image)`: reduce to 9 x 8, one bit per horizontal neighbour pair, row by row, most significant bit first. Done when: a left-to-right gradient gives all zeros and its mirror all ones. Cheaper substitute: an 8 x 8 mean hash, which is far less selective.
- [ ] Add `dt::phash(image)`: reduce to 32 x 32, apply a DCT-II from a fixed cosine table in `double`, take the top-left 8 x 8, set each bit against the median of the block with the DC term left out. Done when: a test against a hand-computed 32 x 32 case matches. Cheaper substitute: a DCT built on fast-math, whose bits differ between builds.
- [ ] Add `dt::hamming(a, b)` with `std::popcount`. Done when: tests cover 0, 1 and 64 bits. Cheaper substitute: a loop over bits.
- [ ] Pin golden values: store the dHash and pHash of three generated scenes in `tests/engine/perceptual_golden.h`. Done when: the test fails if either hash changes by one bit. Cheaper substitute: testing only that hashes are "similar".
- [ ] Assert the fixture behaviour that matching relies on: for every scene, the resize and both recompressions are within 6 pHash bits of the original, and every near-miss pair is more than 12 apart. Done when: the test prints the worst case of each and passes. Cheaper substitute: tuning limits later with no evidence.
- [ ] Commit: `engine: dHash and pHash`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[perceptual]"` passes, and fails when the DC term is included in the pHash median.

## 8. Index database and migrations

Where every photo's facts are kept between scans.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/engine/index.cpp`. Done when: the database opens and creates its tables.
2. Add file rows. Done when: a row round-trips.

- [ ] Add `dt::Index::open(path)` in `src/engine/index.cpp`: create the folder, open SQLite in WAL mode with foreign keys on, and bring the schema to the current `user_version` through numbered forward-only migrations, each in one transaction (foundation plan section 5.6). Done when: a test opens a new database and finds `user_version` 1 and every table of the foundation plan. Cheaper substitute: `CREATE TABLE IF NOT EXISTS` with no version, which cannot change a column later.
- [ ] Refuse, with a distinct `Error`, a file that is not a database, a database from a newer version, and a failed migration, leaving the file untouched. Done when: tests cover the three. Cheaper substitute: deleting and recreating the user's index without asking.
- [ ] Add `upsert_file` and `find_file(path)` for the `files` table, with the hashes as integers and a 32 byte blob. Done when: a row written with every column reads back equal, including a path with non-ASCII characters. Cheaper substitute: storing hashes as text.
- [ ] Add `needs_read(path, size, modified)` returning false only when a row matches all three and has no read error. Done when: tests cover a match, a changed size, a changed time and a row with an error. Cheaper substitute: matching by path alone, which misses an edited photo.
- [ ] Write in batches of 500 rows per transaction. Done when: a test inserting 20,000 rows finishes in under 5 seconds. Cheaper substitute: one transaction per row.
- [ ] Add `clear()` removing every row of every table but keeping the schema. Done when: a test sees empty tables and the same `user_version`. Cheaper substitute: deleting the file while it is open.
- [ ] Commit: `engine: index database and migrations`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[index]"` passes, and fails when `needs_read` ignores the modified time.

## 9. Scan pipeline with progress and cancel

The parts joined: walk, skip what is known, decode, hash, store.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `include/doubletake/scan.h` and `src/engine/scan.cpp`. Done when: a fixture folder is scanned into the index.
2. Add progress and cancel. Done when: both are tested.

- [ ] Add `dt::ScanOptions` (folders, hidden, raw, minimum pixel size) and `dt::scan(options, index, cancel, progress)` in `src/engine/scan.cpp`: count files first, then process them on a pool of `hardware_concurrency - 1` threads, at least one (foundation plan section 5.1). Done when: scanning `build/fixtures/` leaves one `files` row per fixture with both perceptual hashes. Cheaper substitute: a single thread.
- [ ] Skip a file when `needs_read` is false, and count it as skipped. Done when: a second scan of the fixtures decodes no file (checked by a decode counter) and reports every file skipped. Cheaper substitute: rehashing everything on each scan.
- [ ] Compute BLAKE3 only for files whose size is shared by another file in the scan or the index. Done when: a test with three sizes, one shared, hashes exactly the two files that share it. Cheaper substitute: hashing every file.
- [ ] Store a file that fails to decode with its error text, and leave it out of matching. Done when: a damaged fixture has a row with an error and the scan result counts one unreadable file. Cheaper substitute: dropping it silently, so it is retried and fails on every scan.
- [ ] Leave out files whose shorter side is below the minimum pixel size, after decoding their size. Done when: a 32 x 32 fixture is counted as too small at the default 64. Cheaper substitute: filtering by file size in bytes.
- [ ] Publish `dt::ScanProgress` (phase, files read, files total, current folder, unreadable, skipped) at most ten times a second from one place. Done when: a test over 2,000 files receives at most `elapsed x 10 + 2` calls and the last call has read equal to total. Cheaper substitute: a callback per file, which floods the interface.
- [ ] Stop within 500 ms of cancel, with everything already read committed. Done when: a test cancels mid-scan and a rescan skips the files the first one finished. Cheaper substitute: discarding the work done so far.
- [ ] Mark each row with the scan that last saw it, and return the set of rows seen. Done when: a file deleted between scans is absent from the second scan's set but its row remains. Cheaper substitute: deleting unseen rows, which throws away another folder's work.
- [ ] Commit: `engine: scan pipeline with progress and cancel`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[scan]"` passes, and fails when the skip of unchanged files is removed.

## 10. Console program: scan

The engine, run for real without a window.

**Phase:** 1
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `src/cli/doubletake-cli.vcxproj`. Done when: `doubletake-cli scan` prints results.
2. Test it as a program. Done when: its output is checked.

- [ ] Add `src/cli/doubletake-cli.vcxproj` (console program, in the solution, never installed) with `scan <folder>... [--data-dir <dir>] [--hidden] [--no-raw] [--min-size <px>]`, printing a progress line to standard error and a final summary to standard output (foundation plan section 3). Done when: `doubletake-cli scan build\fixtures --data-dir build\cli-test` exits 0 and prints the photo count. Cheaper substitute: a test-only function that no one can run by hand.
- [ ] Add `--json` writing one object per photo (path, size, width, height, the three hashes in hex, error). Done when: the output parses as JSON lines and holds every fixture. Cheaper substitute: a format only this program can read.
- [ ] Exit 2 with a usage line for no folder or an unknown option, and 1 when a folder does not exist. Done when: tests cover both. Cheaper substitute: exit 0 on bad input.
- [ ] Handle Ctrl+C by cancelling the token and exiting 130 after the engine returns. Done when: a manual run interrupted mid-scan leaves a usable index. Cheaper substitute: letting the process die inside a transaction.
- [ ] Add `tests/engine/cli_scan_tests.cpp` running the program as a child process with a 2 minute limit, ending its process tree on timeout and passing `CREATE_NO_WINDOW`. Done when: the test checks the JSON for three known fixtures. Cheaper substitute: testing only the functions behind the program.
- [ ] Commit: `cli: scan command`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only engine -Filter "[cli-scan]"` passes, and fails when `--json` omits the hashes.

## Verification

- `doubletake-cli scan build\fixtures --json` lists every fixture, including the HEIC and DNG samples, with three hashes each, and a second run reports every file skipped.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
