# Select and review a commit's contents

**English** · [Español](../COMMIT-SELECTION.md)

The `/dev-cycle` closeout uses an explicit file list for each logical commit.
Selection preserves staged changes in other files and retains the cycle's scope,
review and test gates.

`agent-kits/shared/scope-check.py` owns projection and revalidation.
`agent-kits/shared/commit-selection.py` is a read-only CLI: it does not stage,
commit or write objects. The orchestrator runs Git after reviewing the result.

## Procedure

1. Choose exact project-relative files. Do not use directories, globs, absolute
   paths or traversal. Explicitly register only selected new files with
   `git --literal-pathspecs add --intent-to-add --pathspec-from-file=- --pathspec-file-nul`.
   Send the list as UTF-8 bytes with a NUL after each name. Do not replace existing
   staging to resolve a conflict.
2. With `$SHAREDKIT` resolved by the cycle, run
   `python3 "$SHAREDKIT/commit-selection.py" preview --root "$PWD" --path <file>`.
   Repeat `--path` for each file. Keep the JSON in a caller-owned temporary outside
   Git. Review `seleccionados`, `no_seleccionados`, `staged_ajenos`, `conflictos`,
   `limites` and the patch. Exit 0 requires no conflicts; it does not replace review
   or establish who staged a change.
3. Immediately before writing the commit, send that same JSON on stdin to
   `python3 "$SHAREDKIT/commit-selection.py" validate --root "$PWD"`.
   Continue only on exit 0. If HEAD, index or selection changed, create and review
   a new preview; never silently replace the reviewed one.
4. Run `git --literal-pathspecs commit --only --pathspec-from-file=- --pathspec-file-nul -m <message>`.
   Send exactly the reviewed names on stdin as UTF-8/NUL. Keep Git's normal hooks.
   Do not use global staging, a manually published temporary index or options
   that bypass verification.
5. Check the actual commit: only selected paths, matching projected blobs and
   modes; other staged entries retain mode/OID/stage and staged contents.
   Selected paths match between HEAD and index without a residual staged reversal.
   If a hook, editor or another process changed the result, report the discrepancy
   without an automatic reset, amend or replacement commit.

Pass filenames as arguments and NUL records, not interpolated shell command text.
In PowerShell, use a binary pipe for the records: text piping may change encoding
or delimiters.

## Results and limits

| Operation | Exit | Meaning |
|---|---|---|
| `preview` | 0 | Projection available without conflicts |
| `preview` | 1 | Declared conflicts; do not commit |
| `preview` | 2 | Invalid selection |
| `validate` | 0 | Snapshot valid against a fresh read |
| `validate` | 1 | Invalid, altered or stale snapshot |
| Both | 3 | Dependency, reading or budget unavailable |

The snapshot contains HEAD, the observed index SHA, file states and modes,
projected blobs and the exact patch in `patch_base64` with `patch_sha256`. `patch`
is a derived display; `patch_display_lossless` states whether it preserves UTF-8
text. Use the base64 bytes and their SHA for exact evidence.

Selected contents are bounded to 8 MiB per side and 32 MiB combined across HEAD
and worktree. Input/output JSON is capped at 64 MiB. A selected custom Git filter
is a conflict; the reader does not execute it to invent a blob. External diff and
textconv are disabled for reading. Python does not open unrelated file bodies,
although Git may read worktree to enumerate changes. Index reading is Git metadata
and is not a metadata sandbox.

Revalidation and committing are separate operations: there is no atomicity against
editors, hooks or arbitrary writers. The full index SHA legitimately changes after
committing; check preserved unrelated entries rather than byte equality of the
entire index. `snapshot_id` establishes integrity of observed content, not
authentication or human approval.

Without the helper or on error, leave the commit pending with its reason. Other
authorized work can continue. Selection alone does not authorize push, merge,
PR or release.
