# How to apply this to `ad-account-management-portal`

This folder contains the files that fix the credibility issues in the repo:
a `.gitignore`, a cleaned-up `config/settings.py` (no more hardcoded secrets),
a `requirements.txt` (didn't exist before), an `.env.example` template, and
three files with `print()` debugging replaced by proper logging
(`accounts/backends.py`, `accounts/views.py`, `core/decorators.py`).

It does **not** include your whole project — just the new/changed files.
You apply it on top of your existing local clone.

## Step 1 — Clone your repo locally (if you don't already have it)

```bash
git clone https://github.com/Dorra29/ad-account-management-portal.git
cd ad-account-management-portal
```

## Step 2 — Copy these files into your clone, overwriting the old ones

Copy everything from this zip into the root of your cloned repo:
- `.gitignore` → repo root
- `.env.example` → repo root
- `requirements.txt` → repo root
- `config/settings.py` → overwrite `config/settings.py`
- `accounts/backends.py` → overwrite `accounts/backends.py`
- `accounts/views.py` → overwrite `accounts/views.py`
- `core/decorators.py` → overwrite `core/decorators.py`

## Step 3 — Create your real `.env` file (this one is NOT committed)

```bash
cp .env.example .env
```

Then open `.env` and fill in the real values. For `DJANGO_SECRET_KEY`, you can use this
freshly generated one (it was generated just now and isn't used anywhere else — treat it
as yours):

```
noTg4qRnO2xuDjvV_8fqnc0qLrwCiaEhzjxL4lNp26Mnoh-BRP-N47lFPrA2tEIZqyc
```

For `LDAP_BIND_PASSWORD`, put your real lab AD password there — **but change it first**
(Step 6 explains why).

## Step 4 — Install the new dependency and stop tracking venv/db/pycache

```bash
pip install -r requirements.txt

# Stop tracking these — .gitignore will keep them out from now on,
# but git still remembers them from before, so remove them from the index:
git rm -r --cached venv
git rm --cached db.sqlite3
git rm -r --cached $(find . -name "__pycache__" -not -path "./venv/*")
```

(If any of those commands say "did not match any files," that's fine — it just means
that particular thing wasn't tracked.)

## Step 5 — Commit and push

```bash
git add .
git commit -m "Remove committed secrets/venv/db, add .gitignore, requirements.txt, and switch debug prints to logging"
git push
```

After this push, anyone opening `config/settings.py` on GitHub will see it reading from
environment variables — no password, no secret key, no debug flag hardcoded.

## Step 6 — Rotate the exposed LDAP password (important, do this regardless of Step 5)

`ITlab123` was live in a **public** repo. Removing it from the current file doesn't erase
it from the repo's commit history — anyone can still find it by browsing old commits.
The fix that actually matters is changing the password on the lab AD server itself, so the
leaked one stops working. Do that in your AD lab environment, then put the *new* password
in your local `.env`.

## Step 7 (optional, more thorough) — scrub the old password out of git history

If you want the string `ITlab123` gone from the repo entirely, not just the current file,
you need to rewrite history. The simplest tool for this is `git filter-repo`:

```bash
pip install git-filter-repo
git filter-repo --replace-text <(echo 'ITlab123==>REDACTED')
git push --force
```

This is optional — once you've rotated the password (Step 6), the old leaked value is
harmless, since it no longer opens anything. Do this step only if you want the history
itself to look clean to anyone browsing commits.

## Step 8 — Fill in the repo's "About" section on GitHub (not a git step)

On the repo page → gear icon next to "About" →
- **Description:** "Django platform for managing user accounts against Active Directory — LDAP authentication, AD group-to-role mapping, and role-based dashboards for admins, managers, and employees."
- **Topics:** `django`, `python`, `ldap`, `active-directory`, `rbac`, `admin-dashboard`

This is currently empty and is one of the first things a visitor sees, even before opening
the README.

---

### What changed and why it matters for credibility

| File | Before | After |
|---|---|---|
| `config/settings.py` | Hardcoded LDAP password, Django secret key, `DEBUG=True` | Everything read from `.env`, nothing sensitive committed |
| `.gitignore` | Didn't exist | `venv/`, `db.sqlite3`, `__pycache__/`, `.env` all excluded |
| `requirements.txt` | Didn't exist | Anyone can `pip install -r requirements.txt` and actually run the project |
| `accounts/backends.py`, `accounts/views.py`, `core/decorators.py` | `print()` debugging left in | Proper `logging` calls — reads like real production code |
