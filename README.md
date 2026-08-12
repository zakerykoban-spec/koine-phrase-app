# Διάλογοι Ἑλληνιστί — Koine Phrase App V2

A mobile-first Koine Greek phrase and mastery study app.

## V2 direction

The original app was a Streamlit prototype. V2 replaces the runtime UI with React + TypeScript + Vite and is designed to deploy as an installable Progressive Web App through GitHub Pages.

The existing JSON files in `decks/` remain the authoritative study content. Vite imports them at build time, so deck content does not need to be rewritten for the web migration.

## Behavior carried forward

- Multi-deck selection
- Greek / English search
- Reveal / hide flashcards
- Favorites
- Greek parsing display
- Mastery sessions
- Correct / missed tracking
- Configurable repeat spacing for missed cards
- Reshuffle and restart flows
- Session summaries

## V2 fixes

- No deck is automatically selected on a first visit.
- Selected decks persist immediately in browser `localStorage` and restore on the next visit.
- Favorites and study settings also persist locally instead of writing a server-side `favorites.json` file.
- Session summaries retain whether a card was missed at least once, even when it is later mastered.

## Visual system

The V2 interface adapts the CENTURION FORGE palette for a focused reading/study application:

- charcoal `#151714`
- warm ivory `#e9dfce`
- muted stone `#9c988d`
- bronze-gold `#d4a45f`
- olive `#4c5232`
- deep blue-green `#274653`

## Local development

Requires Node.js 22+.

```bash
npm install
npm run dev
```

Validation:

```bash
npm run typecheck
npm run build
```

## Deployment

`.github/workflows/deploy-pages.yml` validates pull requests and deploys `dist/` to GitHub Pages whenever `main` is updated.

The Vite base path and PWA scope are configured for:

`/koine-phrase-app/`

## Legacy prototype

The Streamlit files are intentionally retained during the V2 validation branch so the old behavior remains available as a comparison target. They are not part of the V2 web build or deployment path and can be archived or removed after acceptance.
