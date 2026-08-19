import { handleApiRequest, type ApiEnv } from './api'

interface Env extends ApiEnv {
  ASSETS: {
    fetch(request: Request): Promise<Response>
  }
}

const API_PATHS = [
  '/auth/',
  '/me',
  '/stores',
  '/products',
  '/meal-reports',
  '/drink-refills',
  '/inventory-checks',
  '/inventories',
  '/boards/',
  '/users',
  '/roles',
]

function isApiRequest(pathname: string) {
  return API_PATHS.some((path) => pathname === path || pathname.startsWith(path))
}

const SECURITY_HEADERS = {
  'X-Robots-Tag': 'noindex, nofollow, noarchive, nosnippet, noimageindex',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
  'Cache-Control': 'private, no-store',
} as const

function secureResponse(response: Response) {
  const headers = new Headers(response.headers)

  for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
    headers.set(name, value)
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  })
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    if (isApiRequest(url.pathname)) {
      return secureResponse(await handleApiRequest(request, env))
    }

    const assetResponse = await env.ASSETS.fetch(request)
    const lastPathPart = url.pathname.split('/').pop() || ''
    if (request.method === 'GET' && assetResponse.status === 404 && !lastPathPart.includes('.')) {
      const fallbackUrl = new URL('/', request.url)
      return secureResponse(await env.ASSETS.fetch(new Request(fallbackUrl, request)))
    }

    return secureResponse(assetResponse)
  },
}
