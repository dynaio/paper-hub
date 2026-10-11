# Amayas

A research paper vault with hash-locked versions and a submission
safety check. Local-first, single-user, Linux desktop.

## The problem it solves

You finish a paper. You mark it ready. You tell a coauthor. Weeks pass.
You or they edit the file — a different copy, a different folder, a
different device. Then you sit down to submit, and the PDF you upload is
not the version you reviewed.

Amayas makes that specific mistake impossible.

## The one mechanism that matters

- When you mark a version ready, Amayas stores its SHA-256 and writes a
  frozen copy: LOCKED-v3.pdf, chmod 0444.
- When you click Mark as submitted..., Amayas hashes the file you are
  about to submit and compares to the locked hash.
- If it changed, you get a hard stop before anything is uploaded:

    Version mismatch
    The file for v3 has changed since it was locked.
    Locked hash:  a3f1b2c8d9e0
    Current hash: 7d4c1e9a2b83
    [Cancel]  [Override and submit anyway]

That dialog is the entire reason this app exists.

## What it does

- Vault — every paper lives in ~/Papers/files/<id>-<slug>/
- Versions — every drop creates a new version, label auto-assigned
  (v1, v2, revision1, anything you want)
- Hash locking — mark a version ready, its file gets frozen,
  chmod 0444, SHA-256 stored
- Submissions — a permanent frozen copy named
  SUBMITTED-v3-neuro-2026-03-12.pdf, plus a row in the submissions
  table with the hash at submit time
- Attachments — figures, reviewer letters, screenshots; drag onto a card
- Activity timeline — every action logged, never edited
- Statuses — user-editable list (drafting, ready, submitted, in_review,
  revision_requested, accepted, published, ...)
- Categories — user-editable groups (AI, CV, Fire, Calibration, ...)
- Search — title, authors, abstract, tags, remarks
- Drag and drop — drop a document on the top zone to add a paper, drop
  onto a card to add a version
- Cover thumbnails — auto-rendered page 1 for PDFs
- Auto-extract — title, authors, abstract, page count from PDF metadata
  and text

Everything is local. No cloud, no telemetry, no account.

## Install

    git clone https://github.com/dynaio/paper-hub.git
    cd paper-hub
    ./install.sh
    amayas

The installer uses an existing Python venv (~/Code/.venv by default,
override with AMAYAS_VENV=/path/to/venv), checks dependencies, writes a
launcher at ~/.amayas/amayas, symlinks it to /usr/local/bin/amayas, and
registers a .desktop entry so Amayas shows up in the GNOME app list.

## Requirements

- Python 3.10+
- PyQt6, PyMuPDF, Pillow
- Linux desktop (tested on Ubuntu 26.04 / GNOME 46+ / Wayland)

## Where everything lives

    ~/Papers/                              vault
      papers.db                            sqlite - source of truth
      settings.json
      files/
        0001-wildfire-attention/
          v1.pdf
          v2.pdf
          LOCKED-v2.pdf                    frozen, read-only
          SUBMITTED-v2-neuro-2026-03-12.pdf
          cover.png
          attachments/
            fig1.png

    ~/.amayas/                             app state
      amayas                               launcher script
      amayas-icon.png                      your logo
      icons/                               hashed copies for GNOME cache

Back up ~/Papers/ and you keep everything - all files, all versions,
all history.

## The file layout after locking

    v1.pdf                            editable, current draft
    v2.pdf                            editable
    LOCKED-v2.pdf                     frozen at the moment you marked ready
    SUBMITTED-v2-neuro-2026-03-12.pdf permanently frozen, hash recorded

Even if you open the vault in Files and forget what the app knows, the
filenames tell you: this is the ready version, that is the one that went
out.

## Using it

1. Launch amayas.
2. Drop a PDF on the top drop zone, get a new paper card with cover from
   page 1 and metadata extracted.
3. Drop another PDF onto the card for a new version. Check "Make this
   the canonical version" and "Lock this version".
4. Click the card to see the abstract, versions with hash status, and
   the activity timeline.
5. When you are ready to submit, open the paper and click "Mark as
   submitted...". Amayas verifies the hash and, on success, writes a
   SUBMITTED-*.pdf copy plus a submission row.
6. Settings -> Appearance (logo, theme), Statuses, Categories, Behavior
   (autolock, hash verification).

## Settings

- Appearance — app logo, whether to show the brand logo in the toolbar,
  light/dark theme
- Statuses — add, rename, reorder, delete the statuses a paper can be
  in. Existing papers keep whatever status they had.
- Categories — add, rename, delete groups. Papers can have one category
  each.
- Behavior — autolock new versions, verify hash before submission
  (recommended; this is the safety net)

## What is not in this release

- Full-text search inside PDFs
- Symlink views (_by_status/, _by_venue/, _by_year/)
- Embedded PDF reader
- DOCX / PPTX / ODP metadata extraction
- AI extraction and version diffing (planned; will share the same
  provider system as aek at github.com/dynaio/project-hub)
- Windows / macOS port

## Citation

If you use Amayas in academic work, publications, or public projects,
please cite:

    Berassil Abdelkader. Amayas - research paper vault. 2026.
    https://github.com/dynaio/paper-hub

See LICENSE for the full terms.

## License

MIT with a citation requirement. See LICENSE.

Copyright (c) 2026 Berassil Abdelkader.
