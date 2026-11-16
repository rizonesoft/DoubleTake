---
schema_version: 1
id: packaging
domain: 05-release
status: active
title: "TODO-01 -- Packaging and release"
depends_on: ["similar-shots"]
---

# TODO-01 -- Packaging and release

> **Goal:** A Release build is packed into an Inno Setup installer that installs per user, runs and uninstalls cleanly; a tag produces that installer in GitHub Actions; `version.json` tells installed copies a new version exists; and the README shows the real app.

> **Current state:** Measured 2026-11-16. Every page works in Debug (`D03`, `D04`). `resources/installer/` holds the wizard images and `resources/brand/` the icon (`D00 T01 §9`). There is no `installer/` folder, no release workflow and no `version.json`, and the README has no screenshot. Inno Setup 7 is installed at `C:\Program Files\Inno Setup 7` and is not on `PATH`.

## Inputs

- `docs/plans/2026-11-16-doubletake-foundation.md` sections 2 (D7, D9, D10, D12), 4 and 9 (called "the foundation plan" below).
- `design/SPEC.md`, every section, for the sweep in §7.
- -> XREF: D00 T01 §9 -- the icon and wizard images the installer of §3 uses
- -> XREF: D03 T03 §8 -- the update check that reads the `version.json` of §5
- -> XREF: D99 T01 §3 -- the owner publishes the draft release that §5 creates

## Outcome

- `pwsh scripts/package.ps1` writes `build\installer\DoubleTake-<version>-setup.exe`, and the smoke test installs it, starts the app, and uninstalls it.
- Pushing a tag `v<version>` produces the same installer as a draft GitHub release with its SHA-256.

**Adjacency:** list=not-applicable (packaging lists nothing for the user); document=applicable @ D05 T01 §2; settings=not-applicable (the installer has no options beyond its folder); reporting=not-applicable (nothing is summarised); notifications=not-applicable (the update notice is owned by D03 T03 §9); permissions=applicable @ D05 T01 §3; audit=not-applicable (the release workflow's log is the trail); exchange=not-applicable (nothing is imported or exported); reverse=applicable @ D05 T01 §3

**Adjacency rationale:** The licence and third-party notices are the documents the user receives with the app. The installer asks for no administrator rights, which is the permission decision here. Uninstall is the reverse of install, and it leaves the user's index and settings unless asked.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Release build and self-contained output folder | D04 T01 §6 | [ ] |
| 2 | §2 | Third-party notices | §1 | [ ] |
| 3 | §3 | Inno Setup script and package command | §2, D00 T01 §9 | [ ] |
| 4 | §4 | Installer smoke test | §3 | [ ] |
| 5 | §5 | Version file and release workflow | §4 | [ ] |
| 6 | §6 | README with screenshots | §4 | [ ] |
| 7 | §7 | SPEC coverage sweep | §5, §6 | [ ] |

## 1. Release build and self-contained output folder

**Phase:** 5
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Make Release build clean. Done when: tests pass against it.
2. Stage the files to ship. Done when: one folder holds everything the app needs.

- [ ] Build Release with whole-program optimisation and no debug runtime, and run the engine and appcore test programs against it. Done when: `pwsh scripts/check.ps1 -Configuration Release` passes. Cheaper substitute: shipping a configuration no test has run.
- [ ] Add `scripts/stage.ps1` copying to `build\stage\` exactly what ships: `DoubleTake.exe`, the Windows App SDK self-contained files, `onnxruntime.dll`, `DirectML.dll`, the fonts, the strings, `resources/model.json`, `LICENSE.txt` and `NOTICE.txt`, and no test program, `.pdb` or `doubletake-cli.exe`. Done when: a test lists the folder against an expected manifest in `installer/stage-manifest.txt`. Cheaper substitute: packing the whole build output folder.
- [ ] Add `scripts/check-dependents.ps1` running `dumpbin /dependents` on every `.exe` and `.dll` in `build\stage\`, not only the app, and failing on any imported DLL that is neither in the folder nor part of Windows; where a shipped third-party DLL (ONNX Runtime, DirectML, the Windows App SDK's own) needs the Visual C++ runtime, stage Microsoft's redistributable runtime DLLs beside it, app-local, and record that in `NOTICE.md`. Done when: the script exits 0 on the staged folder and exits 1 when a needed DLL is removed from it. Cheaper substitute: checking the app's own executable only, or requiring the user to install a redistributable.
- [ ] Prove it on a machine without the tools: run the staged app in Windows Sandbox, or a clean virtual machine, started from a script, and require the `[launch]` test's window; when neither is available on the build machine, record that in the run file and leave the check to `D99 T01 §3`, whose second-PC install covers it. Done when: the sandbox run passes, or the run file names why it could not run. Cheaper substitute: trusting a developer machine, where every runtime is already installed.
- [ ] Start the staged app from a path with a space and a non-ASCII character, with a fresh data folder. Done when: the `[launch]` UI test passes against `build\stage\`. Cheaper substitute: testing only from the build folder.
- [ ] Keep the `.pdb` files in `build\symbols\<version>\`. Done when: the folder exists after staging. Cheaper substitute: losing the symbols needed to read a crash report.
- [ ] Commit: `release: release build and staged output`

**Test checkpoint:** `pwsh scripts/stage.ps1 -Verify` exits 0, and exits 1 when a file not in `installer/stage-manifest.txt` is in `build\stage\`.

## 2. Third-party notices

**Phase:** 5
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Generate the list. Done when: it matches what is linked.
2. Check licences. Done when: an incompatible one fails the build.

- [ ] Add `scripts/gen-notice.py` building `NOTICE.md` from `vcpkg_installed/` (each port's `copyright` file), the NuGet packages' licence metadata, the font and the model: name, version, licence name and full licence text (foundation plan section 9). Done when: the file lists every library `dumpbin` or the linker map shows in the staged binaries. Cheaper substitute: a hand-kept list that misses a transitive library.
- [ ] Fail when a component's licence is not on an allow-list of GPL-3.0-compatible licences in `scripts/licences-allowed.json`, naming the component (foundation plan D8). Done when: `scripts/tests/test_gen_notice.py` passes and fails with a made-up licence added. Cheaper substitute: finding an incompatible licence after release.
- [ ] Run the generator with `--check` in `scripts/check.ps1`, so a new dependency without a notice fails. Done when: adding a port to `vcpkg.json` without regenerating fails the check. Cheaper substitute: none needed.
- [ ] Commit: `release: generated third-party notices`

**Test checkpoint:** `python scripts/gen-notice.py --check` exits 0, and exits 1 when a vcpkg port is added without regenerating.

## 3. Inno Setup script and package command

**Phase:** 5
**Needs:** windows-host
**Surface:** yes
**Fidelity:** foundation plan section 9, second bullet, and `design/SPEC.md` section 13 (wizard images).
**Job:** the user installs DoubleTake without an administrator prompt and finds it in the Start menu.
**Treatment:** a short wizard in the Darkroom look: welcome, folder, install, finish with "Start DoubleTake". Cheaper substitute that fails: an installer that asks for administrator rights to write to Program Files.
**Chrome:** Inno Setup's modern wizard with the generated wizard images and the app icon.

**Build order:**

1. Add `installer/DoubleTake.iss`. Done when: it compiles.
2. Add `scripts/package.ps1`. Done when: one command writes the installer.

- [ ] Add `installer/DoubleTake.iss`: `PrivilegesRequired=lowest`, default folder `{localappdata}\Programs\DoubleTake`, a fixed `AppId`, the version from a define passed on the command line, the GPL licence page from `LICENSE`, the wizard images and icon from `resources/`, a Start menu entry, an optional desktop icon (off by default), and "Start DoubleTake" on the last page (foundation plan D9). Done when: the Inno Setup compiler compiles it with no warning. Cheaper substitute: an installer that needs elevation.
- [ ] Add `scripts/package.ps1`: build Release, stage, find the Inno Setup compiler through its uninstall registry key and then its default folders, never `PATH`, and compile to `build\installer\DoubleTake-<version>-setup.exe` with the version read from `version.props`. Done when: it writes the file from a plain PowerShell window. Cheaper substitute: a hardcoded compiler path.
- [ ] Close a running DoubleTake before replacing files, using Inno Setup's application mutex support with the mutex of `D02 T01 §7`. Done when: installing over a running copy asks to close it and then succeeds. Cheaper substitute: "file in use" errors.
- [ ] On uninstall remove the program folder and Start menu entry, and ask `Also remove your scan index, settings and logs?` (default No, and always No in a silent uninstall) before touching the data folder. The data folder is `{localappdata}\DoubleTake` unless the uninstaller is given `/DATADIR=<folder>`, and the removal refuses any folder that does not hold the app's own `settings.json`, so a wrong path cannot delete something else. Done when: the script compiles and a silent uninstall leaves the data folder in place. Cheaper substitute: silently deleting the user's History.
- [ ] Write the installer's SHA-256 to `build\installer\DoubleTake-<version>-setup.exe.sha256`. Done when: the file's hash matches `Get-FileHash`. Cheaper substitute: none needed.
- [ ] Leave signing out, with one clearly named hook in `scripts/package.ps1` (`-SignCommand`) that is a no-op when empty (foundation plan D10). Done when: the script runs with no certificate. Cheaper substitute: a build that fails without a certificate. -> XREF: D00 T01 §9
- [ ] Commit: `release: Inno Setup installer and package command`

**Test checkpoint:** `pwsh scripts/package.ps1` exits 0 and writes the installer and its `.sha256`, and exits 1 when `installer/DoubleTake.iss` names a source file that is not staged.

## 4. Installer smoke test

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** no

**Build order:**

1. Add `scripts/smoke-installer.ps1`. Done when: it installs silently and starts the app.
2. Cover uninstall. Done when: nothing is left behind unasked.

- [ ] Add `scripts/smoke-installer.ps1`: run the installer with `/VERYSILENT /SUPPRESSMSGBOXES /DIR=<temp folder>` and a 5 minute limit, then check the files against `installer/stage-manifest.txt` and the Start menu entry. Done when: it exits 0 after a real install. Cheaper substitute: checking only that the installer file exists.
- [ ] Start the installed `DoubleTake.exe` with `--data-dir` in a temporary folder and `--no-update-check`, and run the `[launch]` and `[scan-end]` UI tests against it. Done when: both pass against the installed copy. Cheaper substitute: assuming an app that ran from the build folder runs when installed.
- [ ] Run the uninstaller silently and check the program folder and Start menu entry are gone and the temporary data folder is untouched. Done when: the script asserts all three. Cheaper substitute: none needed.
- [ ] Test the data removal answer only against a disposable folder: install again, create a temporary data folder holding a `settings.json`, run the uninstaller with `/DATADIR=<that folder>` and the removal chosen, and check that folder is gone; then repeat with a folder that has no `settings.json` and check it is refused and left alone. The test never names, reads or changes `%LOCALAPPDATA%\DoubleTake`, and asserts that folder's file list is the same before and after. Done when: the script asserts all four. Cheaper substitute: answering Yes against the real data folder, which would delete the machine owner's own index and History.
- [ ] End every process the script started, with its whole tree, on failure or timeout, and remove the temporary folders. Done when: a forced failure leaves no `DoubleTake.exe` and no installer process. Cheaper substitute: an orphaned installer holding files open.
- [ ] Refuse to run when a real installation with the same `AppId` exists for the current user, naming it, so the test never touches the owner's own copy. Done when: a test with the registry check faked sees the refusal. Cheaper substitute: uninstalling the owner's app.
- [ ] Commit: `release: installer smoke test`

**Test checkpoint:** `pwsh scripts/smoke-installer.ps1` exits 0, and exits 1 when a staged file is removed from the installer script.

## 5. Version file and release workflow

**Phase:** 5
**Needs:** windows-host
**Surface:** no

**Build order:**

1. Add `version.json`. Done when: it names the published version and is checked.
2. Add the release workflow. Done when: a tag produces a draft release.

- [ ] Add `version.json` at the repository root with `version` and `url`. It names the newest published version, which is not the version being built: `main` moves ahead in `version.props` while installed copies must only hear of a version whose installer can be downloaded. Start it at `0.0.0` with the repository's releases page as `url` (foundation plan D12). Done when: the file exists and an app built at `0.1.0` reading it shows no notice. Cheaper substitute: a file that always equals `version.props`, which would announce every version before its installer exists.
- [ ] Add `scripts/gen-version-json.py` with `--publish <version>` (write that version, refusing one above `version.props` or below the file's current one), `--set-url <address>` and `--check` (the file parses, its version is not above `version.props`, and its `url` passes the app's rules), and run `--check` in `scripts/check.ps1`. Done when: `--publish 9.9.9` is refused and `--check` fails on a hand-edited `url` with an `http` address. Cheaper substitute: editing the file by hand at each release.
- [ ] Validate `version.json` against the same rules the app applies (`parse_version_file` of `D03 T03 §8`) in a test. Done when: a `url` on an unknown host fails the test. Cheaper substitute: publishing a file every installed copy will refuse. -> XREF: D03 T03 §8
- [ ] Add `.github/workflows/release.yml` on tags `v*`: refuse a tag that does not equal `v<version.props>`, run `scripts/check.ps1`, run `scripts/package.ps1`, and create a draft GitHub release with the installer, its `.sha256` and notes from `CHANGELOG.md`. Actions are pinned by commit. Done when: a dry run with `act` or a tag on a fork produces the draft; without either, the workflow passes `actionlint` and its script steps pass locally. Cheaper substitute: a release that is published the moment a tag is pushed.
- [ ] Install Inno Setup on the runner at a pinned version with its installer's SHA-256 checked. Done when: the workflow step verifies the hash before running it. Cheaper substitute: an unverified download run in CI.
- [ ] Add `CHANGELOG.md` in the Keep a Changelog form with the `0.1.0` entry, and `docs/release.md` giving the owner's steps in order: set `version.props`, tag, wait for the draft, install it on a second PC, publish the draft, and only then run `python scripts/gen-version-json.py --publish <version>` and push, so installed copies are told after the download exists. Done when: both files exist and the order is stated. Cheaper substitute: announcing a version whose installer is not yet downloadable. -> XREF: D99 T01 §3
- [ ] Commit: `release: version file and release workflow`

**Test checkpoint:** `python scripts/gen-version-json.py --check` exits 0, and exits 1 when `version.json` names a version above `version.props`.

## 6. README with screenshots

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** yes
**Fidelity:** `design/SPEC.md` section 13 (banner) and the captures of `D03 T03 §11`.
**Job:** a visitor to the repository sees what DoubleTake is, what it looks like, and how to get it.
**Treatment:** the banner, one sentence, three real screenshots, download and build instructions. Cheaper substitute that fails: mockup images, which show an app that may not match.
**Chrome:** GitHub Markdown, with images from `resources/brand/` and `docs/screenshots/`.

**Build order:**

1. Add the screenshots. Done when: they come from the capture run.
2. Rewrite the README. Done when: every claim in it is true of the build.

- [ ] Add `scripts/readme-screenshots.ps1` copying the Scan, Review and History captures of the fixtures run from `build/renders/` to `docs/screenshots/`. Done when: the three PNGs are committed and match the current build. Cheaper substitute: screenshots taken by hand once.
- [ ] Rewrite `README.md`: the banner, what it does in two sentences, the screenshots, "Download" (the releases page), "How it works" (hashing, the three closeness settings, the Recycle Bin, History), "Privacy" (everything on the PC; the two network uses named), supported formats, "Build from source", licence. Done when: every format and feature named is covered by a passing test. Cheaper substitute: claims copied from the plan and not checked against the app.
- [ ] State the limits honestly: Windows 10 1809 and later, x64 only, unsigned installer (so Windows SmartScreen will warn), English only. Done when: the four are in the README. Cheaper substitute: letting users discover the SmartScreen warning.
- [ ] Add a check that every image the README references exists and that no line carries an em dash or en dash. Done when: `scripts/check.ps1` fails on a broken image link. Cheaper substitute: none needed.
- [ ] Commit: `docs: README with real screenshots`

**Test checkpoint:** `pwsh scripts/check.ps1 -Only plan` exits 0 with the README check included, and exits 1 when a referenced screenshot is deleted.

## 7. SPEC coverage sweep

**Phase:** 5
**Needs:** windows-host, display-session
**Surface:** no

**Build order:**

1. Trace every SPEC line to a test. Done when: the table is complete.
2. Close the gaps. Done when: nothing is unowned.

- [ ] Write `docs/reviews/spec-coverage.md`: one row per numbered item, bullet and table row of `design/SPEC.md` sections 3 to 14, naming the test or capture that proves it. Done when: no row is empty. Cheaper substitute: a statement that everything is covered.
- [ ] For each row with no proof, add the missing test where the behaviour exists, or file a new section through the `add-todo` skill where it does not. Done when: the table has a proof or a section reference on every row. Cheaper substitute: deleting the row.
- [ ] Do the same for every decision D1 to D13 and every numbered section of the foundation plan. Done when: `docs/reviews/spec-coverage.md` has a second table with no empty row. Cheaper substitute: none needed.
- [ ] Run the whole suite once more on the installed copy: `scripts/check.ps1`, `scripts/capture-all.ps1` and `scripts/smoke-installer.ps1`. Done when: all three exit 0 on the release candidate commit, and `tests/ui/capture-states.json` has no state whose `ready` flag is false. Cheaper substitute: relying on earlier runs of older commits.
- [ ] Commit: `docs: SPEC and plan coverage table`

**Test checkpoint:** `pwsh scripts/check.ps1`, `pwsh scripts/capture-all.ps1` and `pwsh scripts/smoke-installer.ps1` all exit 0 on the same commit, and `docs/reviews/spec-coverage.md` has no row without a proof.

## Verification

- The installer built from a clean clone installs without an administrator prompt, the installed app scans a folder and recycles and restores a copy, and the uninstaller removes it.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
