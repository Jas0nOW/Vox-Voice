
# Repo Backup Policy (PRIVATE)

This repository is a **private backup repo** rooted at `$HOME` (`/home/jannis`). It intentionally tracks selected dot-directories containing agent prompts/memory and selected project trees.

## Intentional Backup Allowlist (Tracked On Purpose)
These directories are intentionally tracked and changes should be visible in `git status`:
- `.claude/` (prompts, memory, session artifacts)
- `.codex/` (prompts, memory, configuration)
- `.gemini/` (prompts, memory, settings)
- `.opencode/` (rules, agent configs, local tooling)
- `.github/` (repo config)
- `Schreibtisch/Work-OS/40_Products/WANDA/wandavoice/` (WANDA Voice app + its `docs/`, `prompts/`, `scripts/`, `tests/`)

If a new directory should be backed up, add it explicitly here and ensure `.gitignore` matches.

## Never Track / Must Sanitize (Credentials / Private Keys)
Do not track plaintext secrets. If any of the following must be backed up, store a **REDACTED** version or an **ENCRYPTED** version (age/gpg) instead.

Forbidden examples (must not be committed as plaintext):
- `~/.ssh/` private keys (e.g. `id_rsa`, `id_ed25519`) and known_hosts with sensitive hosts
- `~/.gnupg/` (private key material)
- Browser profiles, cookies, and session stores (Chrome/Chromium/Firefox profiles)
- Password managers / keyrings (e.g. `~/.password-store/`, GNOME Keyring data)
- OAuth tokens / API keys / bearer tokens / refresh tokens
- Plain `.env` files containing secrets
- App configs known to embed credentials:
  - FileZilla site manager / recent servers if passwords are present
  - GitHub CLI host token files (if present)

## Sanitization Rule
If a forbidden config must be backed up:
1) Remove secrets from the plaintext version (sanitized export), OR
2) Store only an encrypted blob in-repo (age/gpg), and keep plaintext only locally.

Never store tokens/keys/passwords in plaintext in git history.

## NOTE: History Scrub (Do Not Auto-Run)
If plaintext credentials were ever committed, they may still exist in **git history** even after sanitizing the current file.

If this repo was ever pushed to any remote:
- Assume credentials may be compromised and rotate them.
- Consider rewriting history to purge the old secret-bearing blobs.

Guidance only (review before running):
- Remove a path from history: `git filter-repo --path .config/filezilla/recentservers.xml --invert-paths`
- Then re-add only the sanitized version in a new commit.
