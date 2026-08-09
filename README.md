# Community Pulse AI

**Local Community News & Facebook Content Agent** is a Windows-first, local desktop workspace for community administrators. It combines editable community profiles, trusted-source research abstractions, transparent ranking, a safety-oriented post studio, sources, drafts, and local history. It never posts to Facebook automatically.

> Status: production-oriented foundation/MVP. The app is usable offline for profiles and careful pasted-information drafting. Live discovery activates when a supported provider is configured. All externally supplied facts still require administrator review.

## Product workflow

`SELECT COMMUNITY → SELECT DATE/TOPIC → DISCOVER → VERIFY → RANK → SELECT STORY → GENERATE → EDIT → COPY / SAVE`

The seeded profiles cover the ten requested Newark, Essex County, West Orange, schools, housing, transportation, safety, ward, and civic-aspirant communities. They are ordinary SQLite records—not application constants—and can be added, edited, or removed.

## Screenshots

- `docs/screenshots/dashboard.png` *(placeholder—capture on Windows after packaging)*
- `docs/screenshots/post-studio.png` *(placeholder)*
- `docs/screenshots/groups.png` *(placeholder)*

## Architecture

- **UI:** PySide6 main window with a newsroom sidebar, responsive split post studio, rich plain-text editing, clipboard, groups, source watchlist, history, and light/dark themes.
- **Persistence:** SQLAlchemy + per-user SQLite under `%LOCALAPPDATA%` (via `platformdirs`), never Program Files.
- **Research:** a small orchestrator invokes query planning, provider search, locality screening, freshness checks, deduplication, source reliability, and configurable transparent ranking concepts.
- **Providers:** async Tavily, Brave, Serper, and RSS implementations behind `SearchProvider`. Provider code uses timeouts and never attempts to bypass access controls.
- **Writing:** deterministic safe fallback works without AI. Low-confidence material is prominently marked `UNVERIFIED COMMUNITY REPORT`. An OpenAI-backed writer can be added behind the LLM provider boundary without changing UI/domain code.
- **Security:** secrets come from environment variables (or should be entered into the OS keychain); source HTML is sanitized; technical failures are written to the per-user log rather than exposed as stack traces.

### Agent workflow

1. Query Planner builds group/location/topic-aware queries.
2. Search Agent calls the selected provider asynchronously.
3. Relevance Agent screens geographic collisions such as Newark, California.
4. Freshness Agent scores known publication dates and does not infer missing dates.
5. Deduplication Agent collapses near-identical headlines.
6. Verification/Source Reliability Agent gives official records priority.
7. Ranking Agent explains a 0–100 score using freshness 25%, locality 25%, impact 20%, discussion 15%, actionability 10%, and confidence 5%.
8. Writer produces reviewable content.
9. Image provider boundary stores license and attribution metadata (copyrighted news images are not downloaded).
10. Quality policy preserves sources and flags unsupported claims.

## Install and run

Python 3.11+ is supported (3.12 recommended):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -m app.main
```

On first launch the app creates the database and imports starter communities and official sources. Credentials are optional; the post editor, communities, drafts, and history work without them.

## API configuration

Copy `.env.example` to `.env`, select one search provider, and set only its key. `OPENAI_API_KEY` is optional. Never put real values in source control. For distributed builds, use environment variables or Windows Credential Manager/keyring. Model selection uses `COMMUNITY_PULSE_MODEL`.

Supported provider adapters: Tavily, Brave Search, Serper, and RSS/direct feeds. Google CSE settings are reserved for a future adapter. Search services should honor robots directives, licensing, terms, paywalls, authentication, CAPTCHAs, and access controls.

## Communities and trusted sources

Open **Groups** to add, edit, or delete a profile. Topics are comma-separated and drive relevance queries. Open **Sources** to review prioritized, data-driven sources. Source editing and RSS management are represented in the persistence model and provider layer; expose them in a future source dialog using the same repository pattern.

## Post studio

Choose a community and date window. Pasted resident reports are intentionally described as reports, not facts. Add evidence to the separate Sources panel, edit freely, copy to the clipboard, or save a local draft. URLs in source material are never invented. Facebook publishing stays manual: copy the approved post and open the group yourself.

## Tests

```bash
pytest
ruff check app tests
```

Coverage includes freshness, locality, deduplication, reliability, ranking explanations, date extraction, group/topic matching, starter CRUD, safe post output, and a mocked provider contract.

## Windows executable and installer

Install PowerShell, Python 3.12, and optionally Inno Setup 6 (`iscc` on PATH), then run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

The script creates an isolated build environment, runs tests, and builds `dist\CommunityPulseAI.exe`. If Inno Setup is available it also builds `dist\CommunityPulseAI-Setup.exe`, with a Start Menu shortcut and optional Desktop shortcut. Runtime assets are resolved by PyInstaller; writable data remains in the correct user-data directory. macOS/Linux packaging can later reuse the spec and `platformdirs` paths.

## Troubleshooting

- **App opens but discovery is unavailable:** configure one provider key; local features are intentionally still available.
- **Invalid key/quota/no internet:** verify the environment, provider subscription, system clock, and connectivity. Retry later without losing drafts.
- **Website/date/image unavailable:** the app leaves absent metadata unknown rather than guessing. Open the source and verify manually.
- **Startup problem:** inspect the user log directory (`%LOCALAPPDATA%`/platform-specific logs) for `community_pulse.log`.
- **Database reset:** back up the per-user database, close the app, then remove it. The starter records will be imported at next launch.

## Security, safety, and legal notes

Do not paste private or confidential personal data. Validate allegations using authoritative evidence, particularly crime, candidates, schools, businesses, and individuals. Social posts and anonymous complaints are leads. Political content must distinguish fact, claim, opinion, endorsement, and allegation and remain neutral. Never imply a score predicts virality.

The administrator is responsible for copyright and platform compliance. Reuse only official, public-domain, or appropriately licensed images and retain creator/license/attribution. Never republish a news photograph merely because it is visible online. No component bypasses authentication, paywalls, robots restrictions, CAPTCHAs, or site controls. No unauthorized Meta/Facebook automation is included.
