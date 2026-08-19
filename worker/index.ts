interface Env {
  ASSETS: {
    fetch(request: Request): Promise<Response>
  }
  SUPABASE_URL?: string
  SUPABASE_PUBLISHABLE_KEY?: string
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

async function proxyApiRequest(request: Request, env: Env) {
  if (!env.SUPABASE_URL || !env.SUPABASE_PUBLISHABLE_KEY) {
    return Response.json({ detail: 'API service is not configured' }, { status: 503 })
  }

  const sourceUrl = new URL(request.url)
  const functionUrl = new URL(
    `${env.SUPABASE_URL.replace(/\/$/, '')}/functions/v1/private-workspace-api${sourceUrl.pathname}`,
  )
  functionUrl.search = sourceUrl.search

  const upstreamRequest = new Request(functionUrl, request)
  upstreamRequest.headers.set('apikey', env.SUPABASE_PUBLISHABLE_KEY)
  upstreamRequest.headers.delete('host')
  return fetch(upstreamRequest)
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    if (isApiRequest(url.pathname)) {
      return secureResponse(await proxyApiRequest(request, env))
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
