interface Env {
  ASSETS: {
    fetch(request: Request): Promise<Response>
  }
  SUPABASE_URL?: string
  SUPABASE_PUBLISHABLE_KEY?: string
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

function jsonResponse(body: unknown, status = 200) {
  return secureResponse(Response.json(body, { status }))
}

function bearerToken(request: Request) {
  const authorization = request.headers.get('Authorization') || ''
  const match = authorization.match(/^Bearer\s+(.+)$/i)
  return match?.[1] || ''
}

async function fetchCurrentUser(request: Request, env: Env) {
  const accessToken = bearerToken(request)
  if (!accessToken) {
    return jsonResponse({ detail: 'Not authenticated' }, 401)
  }

  const supabaseUrl = env.SUPABASE_URL?.replace(/\/$/, '')
  const publishableKey = env.SUPABASE_PUBLISHABLE_KEY
  if (!supabaseUrl || !publishableKey) {
    return jsonResponse({ detail: 'Authentication service is not configured' }, 503)
  }

  const authResponse = await fetch(`${supabaseUrl}/functions/v1/private-workspace-auth-me`, {
    headers: {
      apikey: publishableKey,
      Authorization: `Bearer ${accessToken}`,
    },
  })
  const headers = new Headers(authResponse.headers)
  headers.delete('set-cookie')
  return secureResponse(new Response(authResponse.body, {
    status: authResponse.status,
    statusText: authResponse.statusText,
    headers,
  }))
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)
    if (request.method === 'GET' && url.pathname === '/auth/me') {
      try {
        return await fetchCurrentUser(request, env)
      } catch {
        return jsonResponse({ detail: 'Authentication service is temporarily unavailable' }, 503)
      }
    }

    if (request.headers.has('Authorization')) {
      return jsonResponse({ detail: 'Backend API is not configured for this deployment' }, 503)
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
