import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import { handleApiRequest, type ApiEnv } from './api.ts'

const FUNCTION_PATH = '/private-workspace-api'

function namedKey(name: string) {
  const raw = Deno.env.get(name)
  if (!raw) return ''

  try {
    const keys = JSON.parse(raw) as Record<string, unknown>
    const candidate = keys.default ?? Object.values(keys).find((value) => typeof value === 'string')
    return typeof candidate === 'string' ? candidate : ''
  } catch {
    return ''
  }
}

function apiEnv(): ApiEnv {
  return {
    SUPABASE_URL: Deno.env.get('SUPABASE_URL'),
    SUPABASE_PUBLISHABLE_KEY:
      namedKey('SUPABASE_PUBLISHABLE_KEYS') || Deno.env.get('SUPABASE_ANON_KEY'),
    SUPABASE_SECRET_KEYS: Deno.env.get('SUPABASE_SECRET_KEYS'),
    SUPABASE_SECRET_KEY: Deno.env.get('SUPABASE_SECRET_KEY'),
    SUPABASE_SERVICE_ROLE_KEY: Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'),
  }
}

Deno.serve((request) => {
  const url = new URL(request.url)
  const functionPathIndex = url.pathname.indexOf(FUNCTION_PATH)
  if (functionPathIndex >= 0) {
    url.pathname = url.pathname.slice(functionPathIndex + FUNCTION_PATH.length) || '/'
  }

  return handleApiRequest(new Request(url, request), apiEnv())
})
