function defaultApiBaseUrl() {
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
  return `${protocol}//${window.location.hostname}:18000`
}

export function apiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim()
  return (configured || defaultApiBaseUrl()).replace(/\/$/, '')
}

export function boardWebSocketUrl(board: string) {
  const url = new URL(apiBaseUrl())
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/ws/boards/${board}`
  url.search = ''
  url.hash = ''
  return url.toString()
}
