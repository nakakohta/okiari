import "jsr:@supabase/functions-js/edge-runtime.d.ts"

type JsonRecord = Record<string, unknown>

function jsonResponse(body: unknown, status = 200) {
  return Response.json(body, {
    status,
    headers: {
      "Cache-Control": "private, no-store",
      "Content-Type": "application/json; charset=utf-8",
      "X-Content-Type-Options": "nosniff",
    },
  })
}

function adminKey() {
  const namedKeys = Deno.env.get("SUPABASE_SECRET_KEYS")
  if (namedKeys) {
    try {
      const parsed = JSON.parse(namedKeys) as Record<string, unknown>
      const candidate = parsed.default ?? Object.values(parsed).find((value) => typeof value === "string")
      if (typeof candidate === "string" && candidate) return candidate
    } catch {
      console.error("supabase_secret_keys_invalid")
    }
  }

  return Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
}

function dataApiHeaders(key: string) {
  const headers: Record<string, string> = { apikey: key }
  if (!key.startsWith("sb_secret_")) {
    headers.Authorization = `Bearer ${key}`
  }
  return headers
}

Deno.serve(async (request) => {
  if (request.method !== "GET") {
    return jsonResponse({ detail: "Method not allowed" }, 405)
  }

  const authorization = request.headers.get("Authorization") ?? ""
  if (!/^Bearer\s+\S+$/i.test(authorization)) {
    return jsonResponse({ detail: "Not authenticated" }, 401)
  }

  const supabaseUrl = (Deno.env.get("SUPABASE_URL") ?? "").replace(/\/$/, "")
  const serviceKey = adminKey()
  if (!supabaseUrl || !serviceKey) {
    console.error("supabase_runtime_not_configured")
    return jsonResponse({ detail: "Authentication service is not configured" }, 503)
  }

  const authResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
    headers: {
      apikey: serviceKey,
      Authorization: authorization,
    },
  })
  if (!authResponse.ok) {
    return jsonResponse({ detail: "Not authenticated" }, 401)
  }

  const authUser = await authResponse.json<{ id?: string }>()
  if (!authUser.id) {
    return jsonResponse({ detail: "Not authenticated" }, 401)
  }

  const userQuery = new URLSearchParams({
    id: `eq.${authUser.id}`,
    select: "id,display_name,email,role_id,is_active,created_at,updated_at,role:app_roles(id,code,name,description,created_at)",
    limit: "1",
  })
  const profileResponse = await fetch(`${supabaseUrl}/rest/v1/app_users?${userQuery}`, {
    headers: dataApiHeaders(serviceKey),
  })
  if (!profileResponse.ok) {
    console.error("profile_query_failed", profileResponse.status)
    return jsonResponse({ detail: "User profile could not be loaded" }, 503)
  }

  const profiles = await profileResponse.json<JsonRecord[]>()
  const profile = profiles[0]
  if (!profile) {
    return jsonResponse({ detail: "Authenticated user is not registered" }, 403)
  }
  if (profile.is_active === false) {
    return jsonResponse({ detail: "Inactive user" }, 403)
  }

  const role = profile.role
  if (!role || typeof role !== "object" || !("code" in role)) {
    return jsonResponse({ detail: "User role is not configured" }, 403)
  }

  const assignmentQuery = new URLSearchParams({
    user_id: `eq.${authUser.id}`,
    select: "store_id,can_view,can_edit",
  })
  const assignmentResponse = await fetch(
    `${supabaseUrl}/rest/v1/user_store_assignments?${assignmentQuery}`,
    { headers: dataApiHeaders(serviceKey) },
  )
  if (!assignmentResponse.ok) {
    console.error("assignment_query_failed", assignmentResponse.status)
    return jsonResponse({ detail: "Store assignments could not be loaded" }, 503)
  }

  return jsonResponse({
    user: profile,
    role,
    store_assignments: await assignmentResponse.json(),
  })
})
