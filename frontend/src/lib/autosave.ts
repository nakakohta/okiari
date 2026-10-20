import axios from 'axios'

export const POSTGRES_INTEGER_MAX = 2_147_483_647

const DEFAULT_DELAY_MS = 450
const MAX_RETRIES = 3

type AutosaveErrorHandler = (willRetry: boolean) => void

interface AutosaveOptions {
  delayMs?: number
  onError?: AutosaveErrorHandler
}

interface AutosaveEntry {
  attempt: number
  generation: number
  onError?: AutosaveErrorHandler
  run: () => Promise<unknown>
  timer: ReturnType<typeof setTimeout> | null
}

function retryDelay(attempt: number) {
  return 1000 * 2 ** attempt
}

function isRetryable(error: unknown) {
  if (!axios.isAxiosError(error)) return false
  const status = error.response?.status
  if (status === undefined) return true
  return status === 408 || status === 425 || status === 429 || status >= 500
}

export function normalizePostgresInteger(value: unknown) {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.min(POSTGRES_INTEGER_MAX, Math.max(0, Math.trunc(number)))
}

export function createAutosaveQueue() {
  const entries = new Map<string, AutosaveEntry>()
  let nextGeneration = 0
  let stopped = false

  async function execute(key: string, generation: number) {
    const entry = entries.get(key)
    if (!entry || entry.generation !== generation) return
    entry.timer = null

    try {
      await entry.run()
      if (entries.get(key)?.generation === generation) entries.delete(key)
    } catch (error) {
      const current = entries.get(key)
      if (!current || current.generation !== generation) return

      const willRetry = !stopped && isRetryable(error) && current.attempt < MAX_RETRIES
      if (current.attempt === 0 || !willRetry) current.onError?.(willRetry)

      if (!willRetry) {
        entries.delete(key)
        return
      }

      const delay = retryDelay(current.attempt)
      current.attempt += 1
      current.timer = setTimeout(() => void execute(key, generation), delay)
    }
  }

  function schedule(key: string, run: () => Promise<unknown>, options: AutosaveOptions = {}) {
    if (stopped) return
    const previous = entries.get(key)
    if (previous?.timer) clearTimeout(previous.timer)

    const generation = ++nextGeneration
    const entry: AutosaveEntry = {
      attempt: 0,
      generation,
      onError: options.onError,
      run,
      timer: null,
    }
    entries.set(key, entry)
    entry.timer = setTimeout(
      () => void execute(key, generation),
      options.delayMs ?? DEFAULT_DELAY_MS,
    )
  }

  function flush(key: string) {
    const entry = entries.get(key)
    if (!entry) return
    if (entry.timer) clearTimeout(entry.timer)
    entry.timer = null
    void execute(key, entry.generation)
  }

  function cancel(key: string) {
    const entry = entries.get(key)
    if (entry?.timer) clearTimeout(entry.timer)
    entries.delete(key)
  }

  function cancelMatching(predicate: (key: string) => boolean) {
    for (const key of entries.keys()) {
      if (predicate(key)) cancel(key)
    }
  }

  function flushAll() {
    for (const key of entries.keys()) flush(key)
  }

  function stop() {
    stopped = true
    for (const entry of entries.values()) {
      if (entry.timer) clearTimeout(entry.timer)
    }
    entries.clear()
  }

  return {
    cancelMatching,
    flush,
    flushAll,
    has: (key: string) => entries.has(key),
    schedule,
    stop,
  }
}
