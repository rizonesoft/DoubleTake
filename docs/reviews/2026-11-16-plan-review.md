# Plan review, 2026-11-16

One independent read-only review of the whole plan before the first run, by Codex (GPT-6 Astra, medium effort) at commit 78a1c07. It returned 22 findings: 14 tagged P1 and 8 tagged P2. Each was checked against the plan and found valid, and all 22 were fixed in the commit that adds this file. The plan was not reviewed again as a whole: each section still gets its own plan review when the run reaches it.

## Findings as returned

1. **P1, D01 T02 section 7:** `SHQueryRecycleBin` reports bin totals, not whether a particular file can be recycled; its success does not cover disabled recycling or oversized files. Require a shell operation that refuses permanent deletion, verify each actual result through the progress sink, and test refusal cases with disposable files. [Microsoft API documentation](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperationprogresssink-postdeleteitem)

2. **P1, D01 T02 section 7:** The keeper guard checks membership in the proposed recycle list, not whether the retained photo still exists and matches the scan. If the keeper disappeared outside the app, recycling the remaining members violates SPEC section 1; revalidate retained copies before moving anything and leave the group untouched when no valid keeper remains.

3. **P1, D01 T02 section 8:** Recording each file *after* it moves leaves a crash window between the shell operation and the database write, contradicting foundation section 5.7’s recovery guarantee. Persist a pending operation before moving the file, record its confirmed bin identity afterward, and reconcile interrupted operations on startup; test interruption between the move and the completion write.

4. **P1, D01 T01 section 10 and D01 T02 section 10:** The file-level verification commands omit `--data-dir`, so they use the owner’s normal database; subsequent `accept`, `recycle` and `restore` commands can operate on existing user state. Give every command in these sequences the same fresh temporary data directory and explicitly assert isolation.

5. **P1, D05 T01 sections 3 and 4:** Section 3 requires testing both uninstall answers, but the deletion target is the real `%LOCALAPPDATA%\DoubleTake`; the smoke test redirects only the application’s data directory. Test the destructive uninstall option in a disposable Windows user or VM, or provide an explicitly isolated installer test configuration whose data target is temporary.

6. **P1, D01 T01 sections 8 and 9:** An unchanged file can have no BLAKE3 because its size was previously unique; adding an identical copy then skips the old file and hashes only the new one, so Exact misses the pair. Separate cached decoding from exact-hash completeness and backfill missing BLAKE3 values when size collisions arise.

7. **P1, D00 T01 section 2 and D05 T01 section 1:** `x64-windows-static-md` builds libraries against the dynamic CRT, while the prescribed Hybrid CRT uses static CRT compilation; this creates incompatible linkage rather than a self-contained release. Choose a consistent CRT strategy for all linked libraries, inspect dependencies of every shipped DLL as well as the executable, and verify on a clean machine. [Triplet definition](https://raw.githubusercontent.com/microsoft/vcpkg/master/triplets/x64-windows-static-md.cmake), [Hybrid CRT requirements](https://github.com/microsoft/WindowsAppSDK/blob/main/docs/Coding-Guidelines/HybridCRT.md)

8. **P1, D00 T01 section 1:** Its negative checkpoint expects an empty solution’s Restore target to fail when `Directory.Build.props` names an invalid toolset, but no project exists to import that file or resolve the compiler. Add a minimal disposable project for this checkpoint, or move compiler-setting verification to section 3.

9. **P1, D02 T01 sections 4, 6, 7 and 8:** These sections require UI-test checkpoints before section 10 creates the test executable and runner integration; section 10 itself depends on the earlier shell work. Introduce the minimal launch harness alongside section 4 and extend it incrementally so each section’s checkpoint exists when executed.

10. **P1, D03 T01 section 3 and D03 T03 sections 10 and 11:** Phase 3 requires a Similar-shots-on capture and every SPEC dialog state while explicitly disabling Similar shots and postponing its dialog until D04 T01 section 5; D04 then depends on those captures passing. Move model-specific acceptance and captures to their implementing sections and reserve the complete capture sweep for afterward.

11. **P1, D04 T01 section 2:** Rejecting every redirect to another host prevents downloading the chosen Hugging Face model, whose contents are served through separate storage/CDN hosts. Pin and validate an explicit HTTPS redirect policy for the selected source, retain size/hash verification, and test the real download chain rather than only a fake response. [Hugging Face download documentation](https://huggingface.co/docs/hub/models-downloading)

12. **P1, D04 T01 section 3 and D03 T01 section 4:** Embedding is placed inside `dt::scan` and must exclude photos already in hash groups, but the existing orchestration forms those groups only after `dt::scan` returns. Assign one owner to the complete sequence: read/hash, form duplicate groups, embed unclaimed photos, form Similar groups, then save the combined result.

13. **P1, D03 T03 section 10:** Rejecting duplicate names and control types anywhere on a page necessarily fails valid repeated controls such as `Remove folder`, `Restore` and `Show files`, which the SPEC explicitly names identically. Check accessible context and use scoped automation IDs for identity instead of requiring globally unique names. [Microsoft UI Automation guidance](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-usefortesting)

14. **P1, D05 T01 section 5:** Requiring `version.json` to equal `version.props` in every checked commit conflicts with main-only development and the instruction to publish the announcement only after the draft release is published. Define a separate published-version update step so main can build the next version without advertising an unavailable installer.

15. **P2, D00 T01 section 2 and D01 T01 sections 3 and 4:** Foundation section 5.2 promises AVIF and WebP, but the manifest specifies no AVIF decoder feature and WebP is allowed to fail when its optional WIC codec is absent. Explicitly enable an AV1 decoder, provide the promised WebP decoding capability on supported Windows installations, and test both formats without optional system codecs. [libheif feature definitions](https://raw.githubusercontent.com/microsoft/vcpkg/master/ports/libheif/vcpkg.json)

16. **P2, D01 T01 section 5 and D03 T02 section 8:** RAW decoding always uses an embedded preview or half-size processing, so requesting a full-resolution image cannot deliver the actual-size comparison required by SPEC section 6. Add a full-resolution RAW decode mode for actual-size viewing, keeping preview/half-size decoding for hashing and fitted views.

17. **P2, D02 T01 section 2:** `ReplaceFile` requires an existing destination, so the prescribed atomic save cannot create `settings.json` on first run or after the bad file is renamed aside. Specify an atomic first-create path as well as replacement, and test both cases. [ReplaceFile documentation](https://learn.microsoft.com/en-us/windows/desktop/api/winbase/nf-winbase-replacefilea)

18. **P2, D01 T01 section 9:** Minimum-pixel filtering is described only after decoding, while unchanged files bypass decoding; changing the threshold can therefore leave cached photos incorrectly included or excluded. Apply current eligibility rules to cached dimensions on every scan and test increasing and decreasing the threshold without changing the photos.

19. **P2, D04 T01 sections 2 and 3:** The prescribed preprocessing resizes the shorter side directly to the model input size with area averaging, whereas the selected model specifies a 256-pixel shorter side followed by a 224-pixel crop and bicubic resampling. Pin the complete preprocessing contract and compare generated tensors and embeddings against the upstream implementation. [Model preprocessing configuration](https://huggingface.co/onnx-community/dinov2-small/blob/main/preprocessor_config.json)

20. **P2, D03 T03 section 6:** The corrupt-index recovery action renames the entire database and creates an empty one while presenting a dialog promising that History is untouched; History consequently disappears from the application. Give recovery a distinct, accurate contract and preserve/recover clean-up records where readable, with explicit treatment of the database’s WAL files.

21. **P2, D00 T01 sections 7 and 8, and D01 T01 sections 3 through 5:** Decoder checkpoints require capture-date/camera metadata and a rotated HEIC “made in the fixture step,” but the fixture sections never create those required cases. Add explicit metadata-bearing and orientation fixtures to their producing sections, including expected upright dimensions and metadata values.

22. **P2, D01 T02 section 9:** Original path plus a two-second deletion-time tolerance is not a unique Recycle Bin identity; repeated recycling of the same path can select a different item and restore the wrong bytes. Persist the actual recycled-item identity returned by the shell, reject ambiguous fallback matches, and test repeated same-path operations. [Shell result identity](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperationprogresssink-postdeleteitem)

HIGHEST: P1