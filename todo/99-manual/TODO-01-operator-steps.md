---
schema_version: 1
id: operator-steps
domain: 99-manual
status: active
title: "TODO-01 -- Operator steps"
---

# TODO-01 -- Operator steps

> **Goal:** The steps only the owner can take are done and recorded: the website address, the social preview image, the first published release, and the code signing decision.

> **Current state:** Measured 2026-11-16. The repository is public at `https://github.com/rizonetech/DoubleTake`. There is no project website yet, no release, and no code signing certificate. The owner deferred code signing on 2026-11-16.

## Inputs

- `docs/plans/2026-11-16-doubletake-foundation.md` section 11 and decisions D7, D10 and D12.
- `docs/release.md`, written by `D05 T01 §5`.
- -> XREF: D03 T03 §7 -- the Website link and the allowed hosts read the address set in §1
- -> XREF: D05 T01 §5 -- the draft release that §3 publishes

## Outcome

- Each step is either done, with the date and what was set, or still waiting on the owner, and none of them holds up the build.

**Adjacency:** all=not-applicable (operator steps outside the app; each changes a setting on GitHub or a build property, and creates no user-facing record)

**Adjacency rationale:** These are one-off actions by the owner. What they change inside the app is owned by the sections they point at.

## Implementation Order

| Order | Section | Deliverable | Depends On | Status |
| ----- | ------- | ----------- | ---------- | ------ |
| 1 | §1 | Website address | -- | [ ] |
| 2 | §2 | Social preview image on GitHub | -- | [ ] |
| 3 | §3 | First release published | -- | [ ] |
| 4 | §4 | Code signing | -- | [ ] |

## 1. Website address

The app's Website link, the download address in `version.json` and the update check's allowed hosts all default to the GitHub repository. The owner wants update traffic on the project website, so its address goes in once it exists.

**Phase:** 99
**Needs:** owner-decision
**Surface:** no

**Build order:**

1. Get the address from the owner. Done when: it is written in `version.props`.
2. Regenerate. Done when: `version.json` points at the website's download page.

- [ ] Record the website's address and its download page's address, as given by the owner, in `version.props` (`DoubleTakeWebsiteUrl`, `DoubleTakeDownloadUrl`). Done when: both are `https` addresses the owner confirmed. Cheaper substitute: a guessed domain.
- [ ] Regenerate `version.json` with `python scripts/gen-version-json.py`. Done when: its `url` is the download page and `python scripts/gen-version-json.py --check` exits 0. Cheaper substitute: editing the file by hand.
- [ ] Commit: `release: project website address`

**Test checkpoint:** `python scripts/gen-version-json.py --check` exits 0, and the `[update]` appcore tests pass with the website's host on the allowed list.

## 2. Social preview image on GitHub

GitHub only takes a repository's social preview through its settings page.

**Phase:** 99
**Needs:** operator
**Surface:** no

**Build order:**

1. Upload the image. Done when: a shared link to the repository shows it.

- [ ] Upload `resources/brand/github-social-preview.png` in the repository's Settings, General, Social preview. Done when: `gh api repos/rizonetech/DoubleTake --jq .open_graph_image_url` (or the page's `og:image`) is no longer GitHub's generated card. Cheaper substitute: none needed.
- [ ] Commit: `docs: record the social preview upload`

**Test checkpoint:** `gh repo view rizonetech/DoubleTake --json openGraphImageUrl --jq .openGraphImageUrl` prints an address under `repository-images.githubusercontent.com`, and prints GitHub's generated card address before the upload.

## 3. First release published

The release workflow makes a draft. Publishing it, and only then telling installed copies, is the owner's call.

**Phase:** 99
**Needs:** operator
**Surface:** no

**Build order:**

1. Publish the draft. Done when: the installer is downloadable.
2. Merge the version file. Done when: installed copies see the new version.

- [ ] Follow `docs/release.md`: review the draft release, download the installer, check its SHA-256 against the attached file, install it on a second PC, then publish. Done when: `gh release view v0.1.0 --json isDraft --jq .isDraft` prints `false`. Cheaper substitute: publishing an installer nobody installed.
- [ ] Commit: `release: 0.1.0 published`

**Test checkpoint:** `gh release view v0.1.0 --json isDraft,assets --jq '.isDraft, (.assets | length)'` prints `false` and `2`, and fails before the release exists.

## 4. Code signing

The installer and executable are unsigned, so Windows SmartScreen warns on first run. The owner chose on 2026-11-16 to decide this later.

**Phase:** 99
**Needs:** owner-decision
**Surface:** no

**Build order:**

1. Get the owner's decision. Done when: it is recorded here.
2. Apply it. Done when: the package command signs, or the README keeps its warning.

- [ ] Record the owner's decision: a certificate and how it is held, or to stay unsigned. Done when: this section states it with its date. Cheaper substitute: assuming a certificate will appear.
- [ ] When a certificate exists, pass its signing command to `scripts/package.ps1 -SignCommand` in the release workflow, with the credential held as a GitHub Actions secret and never printed. Done when: `Get-AuthenticodeSignature` on the installer and on `DoubleTake.exe` reports `Valid`. Cheaper substitute: a certificate file committed to the repository.
- [ ] Commit: `release: code signing decision`

**Test checkpoint:** `Get-AuthenticodeSignature build\installer\DoubleTake-*-setup.exe` reports `Valid` when signing is chosen, and `NotSigned` otherwise, matching the recorded decision.

## Verification

- Each section above carries the date it was done or the reason it still waits.
- `python scripts/todo-graph.py validate` and `python scripts/todo-graph.py plan --check` pass.
