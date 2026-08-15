import { useEffect, useMemo, useState, type ChangeEvent } from 'react'
import { decks as builtInDecks } from './data/decks'
import { normalizeMetaEntries } from './lib/greek'
import { importPhraseDeck } from './lib/importDeck'
import {
  loadFavorites,
  loadImportedDecks,
  loadLastCard,
  loadSelectedDecks,
  loadSettings,
  saveFavorites,
  saveImportedDecks,
  saveLastCard,
  saveSelectedDecks,
  saveSettings,
} from './lib/storage'
import type { PhraseDeck, SessionSummary, StudySession, StudySettings } from './types'

function uniqueAdd(items: string[], value: string) {
  return items.includes(value) ? items : [...items, value]
}

function without(items: string[], value: string) {
  return items.filter((item) => item !== value)
}

function shuffle<T>(items: T[]): T[] {
  const next = [...items]
  for (let index = next.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1))
    ;[next[index], next[swapIndex]] = [next[swapIndex], next[index]]
  }
  return next
}

type ImportStatus = { kind: 'success' | 'error'; message: string } | null

function App() {
  const [importedDecks, setImportedDecks] = useState<PhraseDeck[]>(() => loadImportedDecks())
  const [selectedDeckIds, setSelectedDeckIds] = useState<string[]>(() => loadSelectedDecks())
  const [favorites, setFavorites] = useState<Set<string>>(() => new Set(loadFavorites()))
  const [settings, setSettings] = useState<StudySettings>(() => loadSettings())
  const [currentId, setCurrentId] = useState<string | null>(() => loadLastCard())
  const [query, setQuery] = useState('')
  const [revealed, setRevealed] = useState(false)
  const [libraryOpen, setLibraryOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [homeOpen, setHomeOpen] = useState(false)
  const [session, setSession] = useState<StudySession | null>(null)
  const [summary, setSummary] = useState<SessionSummary | null>(null)
  const [importStatus, setImportStatus] = useState<ImportStatus>(null)

  const availableDecks = useMemo(
    () => [...builtInDecks, ...importedDecks].sort((a, b) => a.label.localeCompare(b.label, 'en')),
    [importedDecks],
  )
  const importedDeckIds = useMemo(() => new Set(importedDecks.map((deck) => deck.id)), [importedDecks])
  const validDeckIds = useMemo(() => new Set(availableDecks.map((deck) => deck.id)), [availableDecks])
  const cardById = useMemo(
    () => new Map(availableDecks.flatMap((deck) => deck.cards).map((card) => [card.id, card])),
    [availableDecks],
  )

  const selectedCards = useMemo(() => {
    const selected = new Set(selectedDeckIds)
    return availableDecks.filter((deck) => selected.has(deck.id)).flatMap((deck) => deck.cards)
  }, [availableDecks, selectedDeckIds])

  const visibleCards = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase()
    if (!needle) return selectedCards
    return selectedCards.filter((card) =>
      card.koine.toLocaleLowerCase().includes(needle)
      || card.english.toLocaleLowerCase().includes(needle)
      || card.tag?.toLocaleLowerCase().includes(needle),
    )
  }, [query, selectedCards])

  const visibleIds = useMemo(() => new Set(visibleCards.map((card) => card.id)), [visibleCards])

  const activeCard = useMemo(() => {
    const sessionId = session?.queue[0]
    if (sessionId) return cardById.get(sessionId) ?? null
    if (currentId && visibleIds.has(currentId)) return cardById.get(currentId) ?? null
    return visibleCards[0] ?? null
  }, [cardById, currentId, session, visibleCards, visibleIds])

  const activeMeta = useMemo(() => normalizeMetaEntries(activeCard?.meta), [activeCard])

  const favoriteCardsInView = useMemo(
    () => visibleCards.filter((card) => favorites.has(card.id)),
    [favorites, visibleCards],
  )

  const activeStudySetTitle = useMemo(() => {
    if (homeOpen) return 'Koine phrase study'
    if (activeCard) return activeCard.deckLabel
    if (selectedDeckIds.length === 1) {
      return availableDecks.find((deck) => deck.id === selectedDeckIds[0])?.label ?? 'Selected deck'
    }
    if (selectedDeckIds.length > 1) return `${selectedDeckIds.length} decks selected`
    return 'Select a deck to begin'
  }, [activeCard, availableDecks, homeOpen, selectedDeckIds])

  useEffect(() => {
    setSelectedDeckIds((current) => {
      const next = current.filter((id) => validDeckIds.has(id))
      const unchanged = next.length === current.length && next.every((id, index) => id === current[index])
      return unchanged ? current : next
    })
  }, [validDeckIds])

  useEffect(() => {
    saveImportedDecks(importedDecks)
  }, [importedDecks])

  useEffect(() => {
    saveSelectedDecks(selectedDeckIds)
  }, [selectedDeckIds])

  useEffect(() => {
    saveFavorites([...favorites])
  }, [favorites])

  useEffect(() => {
    saveSettings(settings)
  }, [settings])

  useEffect(() => {
    if (session) return
    if (currentId && visibleIds.has(currentId)) return
    setCurrentId(visibleCards[0]?.id ?? null)
  }, [currentId, session, visibleCards, visibleIds])

  useEffect(() => {
    saveLastCard(activeCard?.id ?? null)
  }, [activeCard?.id])

  function closeDrawers() {
    setLibraryOpen(false)
    setMenuOpen(false)
  }

  function openLibrary() {
    setMenuOpen(false)
    setLibraryOpen(true)
  }

  function goHome() {
    setHomeOpen(true)
    closeDrawers()
    setQuery('')
    setSession(null)
    setSummary(null)
    setRevealed(false)
  }

  function toggleDeck(deckId: string) {
    setSelectedDeckIds((current) =>
      current.includes(deckId)
        ? current.filter((id) => id !== deckId)
        : [...current, deckId],
    )
    setHomeOpen(false)
    setSession(null)
    setSummary(null)
    setRevealed(false)
  }

  function clearDecks() {
    setSelectedDeckIds([])
    setHomeOpen(true)
    setSession(null)
    setSummary(null)
    setCurrentId(null)
    setRevealed(false)
  }

  function updateSetting<K extends keyof StudySettings>(key: K, value: StudySettings[K]) {
    setSettings((current) => ({ ...current, [key]: value }))
  }

  async function handleDeckImport(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget
    const file = input.files?.[0]
    if (!file) return

    setImportStatus(null)
    try {
      const deck = await importPhraseDeck(file)
      setImportedDecks((current) => [...current, deck])
      setSelectedDeckIds((current) => uniqueAdd(current, deck.id))
      setCurrentId(deck.cards[0]?.id ?? null)
      setHomeOpen(false)
      setSession(null)
      setSummary(null)
      setQuery('')
      setRevealed(false)
      setImportStatus({
        kind: 'success',
        message: `${deck.label} imported with ${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}.`,
      })
    } catch (error) {
      setImportStatus({
        kind: 'error',
        message: error instanceof Error ? error.message : 'This deck could not be imported.',
      })
    } finally {
      input.value = ''
    }
  }

  function removeImportedDeck(deck: PhraseDeck) {
    const removedCardIds = new Set(deck.cards.map((card) => card.id))
    setImportedDecks((current) => current.filter((item) => item.id !== deck.id))
    setSelectedDeckIds((current) => current.filter((id) => id !== deck.id))
    setFavorites((current) => new Set([...current].filter((id) => !removedCardIds.has(id))))
    if (currentId && removedCardIds.has(currentId)) setCurrentId(null)
    setSession(null)
    setSummary(null)
    setRevealed(false)
    setImportStatus({ kind: 'success', message: `${deck.label} removed from this device.` })
  }

  function browse(delta: number) {
    if (session || visibleCards.length === 0) return
    const index = visibleCards.findIndex((card) => card.id === activeCard?.id)
    const safeIndex = index < 0 ? 0 : index
    const nextIndex = (safeIndex + delta + visibleCards.length) % visibleCards.length
    setCurrentId(visibleCards[nextIndex].id)
    if (settings.autoHide) setRevealed(false)
  }

  function toggleFavorite() {
    if (!activeCard) return
    setFavorites((current) => {
      const next = new Set(current)
      if (next.has(activeCard.id)) next.delete(activeCard.id)
      else next.add(activeCard.id)
      return next
    })
  }

  function startSession(ids: string[]) {
    const sourceIds = [...new Set(ids)].filter((id) => cardById.has(id))
    if (sourceIds.length === 0) return
    const queue = shuffle(sourceIds)
    setHomeOpen(false)
    setSession({
      queue,
      total: sourceIds.length,
      correct: [],
      incorrect: [],
      missedOnce: [],
      repeatEvents: 0,
      sourceIds,
    })
    setSummary(null)
    setCurrentId(queue[0])
    setRevealed(false)
  }

  function endSession() {
    setSession(null)
    setRevealed(false)
  }

  function reshuffleSession() {
    if (!session || session.queue.length < 2) return
    const queue = shuffle(session.queue)
    setSession({ ...session, queue })
    setCurrentId(queue[0])
    setRevealed(false)
  }

  function markCorrect() {
    if (!activeCard) return
    if (!session) {
      browse(1)
      return
    }

    const cardId = activeCard.id
    const queue = session.queue.filter((id) => id !== cardId)
    const nextSession: StudySession = {
      ...session,
      queue,
      correct: uniqueAdd(session.correct, cardId),
      incorrect: without(session.incorrect, cardId),
    }

    if (queue.length === 0) {
      setSummary({
        total: session.total,
        firstPassCorrect: Math.max(0, session.total - session.missedOnce.length),
        missed: session.missedOnce.length,
        repeatEvents: session.repeatEvents,
        missedIds: session.missedOnce,
        sourceIds: session.sourceIds,
      })
      setSession(null)
    } else {
      setSession(nextSession)
      setCurrentId(queue[0])
    }
    setRevealed(false)
  }

  function markIncorrect() {
    if (!activeCard) return
    if (!session) {
      browse(1)
      return
    }

    const cardId = activeCard.id
    const queue = session.queue.filter((id) => id !== cardId)
    const insertAt = Math.min(settings.repeatAfter, queue.length)
    queue.splice(insertAt, 0, cardId)

    setSession({
      ...session,
      queue,
      correct: without(session.correct, cardId),
      incorrect: uniqueAdd(session.incorrect, cardId),
      missedOnce: uniqueAdd(session.missedOnce, cardId),
      repeatEvents: session.repeatEvents + 1,
    })
    setCurrentId(queue[0])
    setRevealed(false)
  }

  const showAnswer = Boolean(activeCard) && (!settings.flashcardMode || revealed)
  const currentPosition = activeCard
    ? visibleCards.findIndex((card) => card.id === activeCard.id) + 1
    : 0
  const sessionProgress = session
    ? Math.max(0, Math.min(1, (session.total - session.queue.length) / Math.max(1, session.total)))
    : 0
  const summaryAccuracy = summary
    ? Math.round((summary.firstPassCorrect / Math.max(1, summary.total)) * 100)
    : 0

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="home-button" type="button" onClick={goHome} aria-label="Return home" title="Home">
          <span lang="grc">Οἶκος</span>
        </button>

        <div className="brand brand-centered">
          <p className="brand-kicker">Koine study</p>
          <h1 lang="grc">Διάλογοι Ἑλληνιστί</h1>
        </div>

        <button
          className={`menu-button ${menuOpen ? 'active' : ''}`}
          type="button"
          onClick={() => {
            setLibraryOpen(false)
            setMenuOpen((value) => !value)
          }}
          aria-label="Open menu"
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>
      </header>

      <div className="app-body">
        <aside className={`sidebar ${libraryOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <div>
              <p className="section-label">Library</p>
              <h2>Choose decks</h2>
            </div>
            <button className="close-sidebar" type="button" onClick={() => setLibraryOpen(false)} aria-label="Close library">×</button>
          </div>

          <div className="deck-summary">
            <span>{selectedDeckIds.length ? `${selectedDeckIds.length} selected` : 'Nothing selected'}</span>
            {selectedDeckIds.length > 0 && <button type="button" onClick={clearDecks}>Clear</button>}
          </div>

          <div className="import-panel">
            <label className="import-deck-button">
              <input
                type="file"
                accept=".json,.csv,.tsv,.txt,application/json,text/csv,text/tab-separated-values,text/plain"
                onChange={(event) => void handleDeckImport(event)}
              />
              <span>Import deck</span>
            </label>
            <p>JSON, CSV, TSV, or TXT. Use Greek/Koine and English/Translation columns; headerless two-column files also work.</p>
            {importStatus && <p className={`import-status ${importStatus.kind}`}>{importStatus.message}</p>}
          </div>

          <div className="deck-list">
            {availableDecks.map((deck) => {
              const selected = selectedDeckIds.includes(deck.id)
              const imported = importedDeckIds.has(deck.id)
              return (
                <div className={`deck-row-shell ${imported ? 'imported' : ''}`} key={deck.id}>
                  <button
                    className={`deck-row ${selected ? 'selected' : ''}`}
                    type="button"
                    onClick={() => toggleDeck(deck.id)}
                    aria-pressed={selected}
                  >
                    <span className="deck-check" aria-hidden="true">{selected ? '✓' : ''}</span>
                    <span className="deck-copy">
                      <strong>{deck.label}</strong>
                      <small>{deck.cards.length} cards{imported ? ' · imported' : ''}</small>
                    </span>
                  </button>
                  {imported && (
                    <button
                      className="remove-deck-button"
                      type="button"
                      onClick={() => removeImportedDeck(deck)}
                      aria-label={`Remove ${deck.label}`}
                      title="Remove imported deck"
                    >
                      ×
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </aside>

        <aside className={`settings-drawer ${menuOpen ? 'open' : ''}`} aria-hidden={!menuOpen}>
          <div className="sidebar-header">
            <div>
              <p className="section-label">Menu</p>
              <h2>Study controls</h2>
            </div>
            <button className="close-sidebar menu-close" type="button" onClick={() => setMenuOpen(false)} aria-label="Close menu">×</button>
          </div>

          <button className="menu-library-action" type="button" onClick={openLibrary}>
            <span>
              <strong>Library</strong>
              <small>Choose or import decks</small>
            </span>
            <span aria-hidden="true">→</span>
          </button>

          <div className="menu-deck-status">
            <span>{selectedDeckIds.length} {selectedDeckIds.length === 1 ? 'deck' : 'decks'}</span>
            <span>{selectedCards.length} cards</span>
          </div>

          <div className="settings-panel menu-settings">
            <p className="section-label">Study settings</p>
            <label className="setting-row">
              <span>
                <strong>Flashcard mode</strong>
                <small>Hide English until reveal</small>
              </span>
              <input
                type="checkbox"
                checked={settings.flashcardMode}
                onChange={(event) => updateSetting('flashcardMode', event.target.checked)}
              />
            </label>
            <label className="setting-row">
              <span>
                <strong>Auto-hide</strong>
                <small>Hide answer on the next card</small>
              </span>
              <input
                type="checkbox"
                checked={settings.autoHide}
                onChange={(event) => updateSetting('autoHide', event.target.checked)}
              />
            </label>
            <label className="setting-row">
              <span>
                <strong>Parsing</strong>
                <small>Show analysis after reveal</small>
              </span>
              <input
                type="checkbox"
                checked={settings.showParsing}
                onChange={(event) => updateSetting('showParsing', event.target.checked)}
              />
            </label>
            <label className="repeat-setting">
              <span>
                <strong>Repeat missed after</strong>
                <small>{settings.repeatAfter} cards</small>
              </span>
              <input
                type="range"
                min="0"
                max="8"
                value={settings.repeatAfter}
                onChange={(event) => updateSetting('repeatAfter', Number(event.target.value))}
              />
            </label>
          </div>
        </aside>

        {(libraryOpen || menuOpen) && (
          <button className="drawer-scrim" type="button" aria-label="Close menu" onClick={closeDrawers} />
        )}

        <main className="workspace">
          <div className="workspace-toolbar">
            <div>
              <p className="section-label">Active study set</p>
              <h2>{activeStudySetTitle}</h2>
            </div>
            <label className="search-field">
              <span className="visually-hidden">Search Greek or English</span>
              <input
                type="search"
                placeholder="Search Greek or English…"
                value={query}
                disabled={homeOpen || selectedDeckIds.length === 0 || Boolean(session)}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
          </div>

          {homeOpen ? (
            <section className="empty-state">
              <p className="card-eyebrow">Time to study</p>
              <h3 lang="grc">Ἀρχώμεθα.</h3>
              <p>
                {selectedDeckIds.length
                  ? `${selectedDeckIds.length} ${selectedDeckIds.length === 1 ? 'deck is' : 'decks are'} ready when you are.`
                  : 'Choose a deck from the library to begin.'}
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
                {selectedDeckIds.length > 0 && <button type="button" onClick={() => setHomeOpen(false)}>Continue study</button>}
                <button type="button" onClick={openLibrary}>Open library</button>
              </div>
            </section>
          ) : selectedDeckIds.length === 0 ? (
            <section className="empty-state">
              <p className="card-eyebrow">Time to study</p>
              <h3 lang="grc">Ἀρχώμεθα.</h3>
              <p>Choose a deck from the library to begin.</p>
              <button type="button" onClick={openLibrary}>Open library</button>
            </section>
          ) : visibleCards.length === 0 ? (
            <section className="empty-state">
              <p className="card-eyebrow">No matches</p>
              <h3>Nothing matches this search.</h3>
              <p>Clear the search field to return to the selected decks.</p>
              <button type="button" onClick={() => setQuery('')}>Clear search</button>
            </section>
          ) : (
            <>
              <section className="study-controls" aria-label="Study session controls">
                <div className="control-group">
                  <button type="button" onClick={() => startSession(visibleCards.map((card) => card.id))} disabled={Boolean(session)}>
                    Study current view
                  </button>
                  <button type="button" onClick={() => startSession(favoriteCardsInView.map((card) => card.id))} disabled={Boolean(session) || favoriteCardsInView.length === 0}>
                    Study favorites
                  </button>
                </div>
                {session && (
                  <div className="control-group secondary">
                    <button type="button" onClick={reshuffleSession}>Reshuffle</button>
                    <button type="button" onClick={endSession}>End session</button>
                  </div>
                )}
              </section>

              {session && (
                <section className="session-strip" aria-label="Session progress">
                  <div className="progress-track"><span style={{ width: `${sessionProgress * 100}%` }} /></div>
                  <div className="session-stats">
                    <span>Remaining <strong>{session.queue.length}</strong></span>
                    <span>Correct <strong>{session.correct.length}</strong></span>
                    <span>Missed <strong>{session.missedOnce.length}</strong></span>
                    <span>Repeats <strong>{session.repeatEvents}</strong></span>
                  </div>
                </section>
              )}

              {summary && !session && (
                <section className="summary-card">
                  <div>
                    <p className="card-eyebrow">Session complete</p>
                    <h3>{summaryAccuracy}% first-pass accuracy</h3>
                    <p>{summary.firstPassCorrect} of {summary.total} cards were correct before needing a repeat.</p>
                  </div>
                  <dl>
                    <div><dt>Total</dt><dd>{summary.total}</dd></div>
                    <div><dt>Missed once</dt><dd>{summary.missed}</dd></div>
                    <div><dt>Repeat events</dt><dd>{summary.repeatEvents}</dd></div>
                  </dl>
                  <div className="summary-actions">
                    <button type="button" disabled={summary.missedIds.length === 0} onClick={() => startSession(summary.missedIds)}>Study missed</button>
                    <button type="button" onClick={() => startSession(summary.sourceIds)}>Restart session</button>
                  </div>
                </section>
              )}

              {activeCard && (
                <article className="study-card">
                  <div className="card-topline">
                    <span>{activeCard.deckLabel}</span>
                    <span>{session ? `Mastery · ${session.queue.length} remaining` : `${currentPosition} / ${visibleCards.length}`}</span>
                  </div>

                  {activeCard.tag && <p className="card-tag">{activeCard.tag}</p>}
                  <div className="greek-text" lang="grc">{activeCard.koine || '—'}</div>

                  {settings.flashcardMode && (
                    <button className="reveal-button" type="button" onClick={() => setRevealed((value) => !value)}>
                      {revealed ? 'Hide answer' : 'Reveal answer'}
                    </button>
                  )}

                  <div className={`answer-region ${showAnswer ? 'visible' : ''}`} aria-hidden={!showAnswer}>
                    {showAnswer && (
                      <>
                        <div className="english-text">{activeCard.english || '—'}</div>
                        {settings.showParsing && activeMeta.length > 0 && (
                          <section className="parse-panel">
                            <p className="parse-title">Ἡ ἀνάλυσις</p>
                            <dl>
                              {activeMeta.map(([key, value]) => (
                                <div key={key}>
                                  <dt>{key}</dt>
                                  <dd>{value}</dd>
                                </div>
                              ))}
                            </dl>
                          </section>
                        )}
                      </>
                    )}
                  </div>

                  <div className="card-actions">
                    <button type="button" className="quiet-action" onClick={() => browse(-1)} disabled={Boolean(session)}>Previous</button>
                    <button type="button" className={`favorite-action ${favorites.has(activeCard.id) ? 'active' : ''}`} onClick={toggleFavorite}>
                      {favorites.has(activeCard.id) ? 'Favorited' : 'Favorite'}
                    </button>
                    <button type="button" className="again-action" onClick={markIncorrect}>{session ? 'Again' : 'Next'}</button>
                    <button type="button" className="known-action" onClick={markCorrect}>{session ? 'Known' : 'Next'}</button>
                  </div>
                </article>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
