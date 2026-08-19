interface Env {
  ASSETS: {
    fetch(request: Request): Promise<Response>
  }
  SUPABASE_URL?: string
  SUPABASE_PUBLISHABLE_KEY?: string
  SUPABASE_SERVICE_ROLE_KEY?: string
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
  const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY
  if (!supabaseUrl || !publishableKey || !serviceRoleKey) {
    return jsonResponse({ detail: 'Authentication service is not configured' }, 503)
  }

  const authResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
    headers: {
      apikey: publishableKey,
      Authorization: `Bearer ${accessToken}`,
    },
  })
  if (!authResponse.ok) {
    return jsonResponse({ detail: 'Not authenticated' }, 401)
  }

  const authUser = await authResponse.json<{ id?: string }>()
  if (!authUser.id) {
    return jsonResponse({ detail: 'Not authenticated' }, 401)
  }

  const serviceHeaders = {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
  }
  const userQuery = new URLSearchParams({
    id: `eq.${authUser.id}`,
    select: 'id,display_name,email,role_id,is_active,created_at,updated_at,role:app_roles(id,code,name,description,created_at)',
    limit: '1',
  })
  const profileResponse = await fetch(`${supabaseUrl}/rest/v1/app_users?${userQuery}`, {
    headers: serviceHeaders,
  })
  if (!profileResponse.ok) {
    return jsonResponse({ detail: 'User profile could not be loaded' }, 503)
  }

  const profiles = await profileResponse.json<Array<Record<string, unknown>>>()
  const profile = profiles[0]
  if (!profile) {
    return jsonResponse({ detail: 'Authenticated user is not registered' }, 403)
  }
  if (profile.is_active === false) {
    return jsonResponse({ detail: 'Inactive user' }, 403)
  }

  const role = profile.role
  if (!role || typeof role !== 'object' || !('code' in role)) {
    return jsonResponse({ detail: 'User role is not configured' }, 403)
  }

  const assignmentQuery = new URLSearchParams({
    user_id: `eq.${authUser.id}`,
    select: 'store_id,can_view,can_edit',
  })
  const assignmentResponse = await fetch(
    `${supabaseUrl}/rest/v1/user_store_assignments?${assignmentQuery}`,
    { headers: serviceHeaders },
  )
  if (!assignmentResponse.ok) {
    return jsonResponse({ detail: 'Store assignments could not be loaded' }, 503)
  }

  const storeAssignments = await assignmentResponse.json()
  return jsonResponse({
    user: profile,
    role,
    store_assignments: storeAssignments,
  })
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

    return secureResponse(await env.ASSETS.fetch(request))
  },
}
