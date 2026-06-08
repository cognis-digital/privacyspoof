# Session & cookie isolation playbook

Spoofing the UA/geo is pointless if your cookies and storage link sessions together.

## Containerize
- **Firefox Multi-Account Containers** / `contextualIdentities` — one container per identity.
- **Chrome profiles** — separate profile per persona (separate cookie jars).
- **Temporary Containers** add-on — auto-disposable containers per tab.

## Clear / partition
- Enable **first-party isolation** / **state partitioning** (Firefox `privacy.partition.network_state`).
- Clear cookies + DOM storage on close; block third-party cookies entirely.
- Use distinct sessions for distinct identities — never reuse a cookie jar across spoofed personas.

## Don't undo your own work
- Logging into a real account inside a spoofed session de-anonymizes it instantly.
- Keep UA + platform + timezone + locale + geo **mutually consistent** per persona.
