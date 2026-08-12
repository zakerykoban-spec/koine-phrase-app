const KEY_MAP: Record<string, string> = {
  lemma: 'λέμμα',
  lem: 'λέμμα',
  'λῆμμα': 'λέμμα',
  'λέμμα': 'λέμμα',
  pos: 'μέρος λόγου',
  part_of_speech: 'μέρος λόγου',
  'μέρος λόγου': 'μέρος λόγου',
  gender: 'γένος',
  'γένος': 'γένος',
  case: 'πτῶσις',
  'πτῶσις': 'πτῶσις',
  number: 'ἀριθμός',
  'ἀριθμός': 'ἀριθμός',
  person: 'πρόσωπον',
  'πρόσωπον': 'πρόσωπον',
  tense: 'χρόνος',
  'χρόνος': 'χρόνος',
  aspect: 'ἄσπεκτος',
  'ἄσπεκτος': 'ἄσπεκτος',
  mood: 'ἔγκλισις',
  'ἔγκλισις': 'ἔγκλισις',
  voice: 'φωνή',
  'φωνή': 'φωνή',
  degree: 'βαθμός',
  'βαθμός': 'βαθμός',
  dialect: 'διάλεκτος',
  'διάλεκτος': 'διάλεκτος',
  note: 'σχόλιον',
  'σχόλιον': 'σχόλιον',
}

const VALUE_MAP: Record<string, Record<string, string>> = {
  'γένος': {
    masculine: 'ἀρσενικόν', feminine: 'θηλυκόν', neuter: 'οὐδέτερον',
    m: 'ἀρσενικόν', f: 'θηλυκόν', n: 'οὐδέτερον',
  },
  'ἀριθμός': {
    singular: 'ἑνικός', plural: 'πληθυντικός', dual: 'δυϊκός',
    sg: 'ἑνικός', pl: 'πληθυντικός',
  },
  'πτῶσις': {
    nominative: 'ὀνομαστική', genitive: 'γενική', dative: 'δοτική',
    accusative: 'αἰτιατική', vocative: 'κλητική',
    nom: 'ὀνομαστική', gen: 'γενική', dat: 'δοτική', acc: 'αἰτιατική', voc: 'κλητική',
  },
  'πρόσωπον': {
    '1': 'πρῶτον', '2': 'δεύτερον', '3': 'τρίτον',
    first: 'πρῶτον', second: 'δεύτερον', third: 'τρίτον',
    '1st': 'πρῶτον', '2nd': 'δεύτερον', '3rd': 'τρίτον',
  },
  'ἔγκλισις': {
    indicative: 'ὁριστική', subjunctive: 'ὑποτακτική', optative: 'εὐκτική',
    imperative: 'προστακτική', infinitive: 'ἀπαρέμφατον', participle: 'μετοχή',
  },
  'φωνή': {
    active: 'ἐνεργητική', middle: 'μέση', passive: 'παθητική',
    act: 'ἐνεργητική', mid: 'μέση', pass: 'παθητική',
  },
  'χρόνος': {
    present: 'ἐνεστώς', imperfect: 'παρατατικός', aorist: 'ἀόριστος',
    perfect: 'παρακείμενος', pluperfect: 'ὑπερσυντέλικος', future: 'μέλλων',
    pres: 'ἐνεστώς', impf: 'παρατατικός', aor: 'ἀόριστος',
    perf: 'παρακείμενος', plup: 'ὑπερσυντέλικος', fut: 'μέλλων',
  },
}

const PREFERRED = [
  'λέμμα', 'μέρος λόγου', 'γένος', 'πτῶσις', 'ἀριθμός', 'πρόσωπον',
  'χρόνος', 'ἄσπεκτος', 'ἔγκλισις', 'φωνή', 'βαθμός', 'διάλεκτος', 'σχόλιον',
]

function stringifyValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(stringifyValue).join(', ')
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value).trim()
}

function normalizeValue(key: string, value: unknown): string {
  const mapper = VALUE_MAP[key]
  const raw = stringifyValue(value)
  if (!mapper || !raw) return raw
  return mapper[raw.toLowerCase()] ?? raw
}

export function normalizeMetaEntries(meta?: Record<string, unknown>): Array<[string, string]> {
  if (!meta) return []

  const normalized = new Map<string, string>()
  Object.entries(meta).forEach(([rawKey, rawValue]) => {
    if (rawValue === null || rawValue === undefined || rawValue === '') return
    const key = KEY_MAP[rawKey.trim()] ?? rawKey.trim()
    const value = normalizeValue(key, rawValue)
    if (value) normalized.set(key, value)
  })

  return [...normalized.entries()].sort(([a], [b]) => {
    const ai = PREFERRED.indexOf(a)
    const bi = PREFERRED.indexOf(b)
    if (ai === -1 && bi === -1) return a.localeCompare(b)
    if (ai === -1) return 1
    if (bi === -1) return -1
    return ai - bi
  })
}
