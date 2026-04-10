import type { NextRequest } from "next/server"
import { NextResponse } from "next/server"
import { getServerSession } from "next-auth/next"

import { authOptions } from "@/lib/auth"

export const dynamic = "force-dynamic"

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
])

async function proxyRequest(request: NextRequest, pathSegments: string[]) {
  const session = await getServerSession(authOptions)
  if (!session) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 })
  }

  const apiUrl = process.env.API_URL
  const apiKey = process.env.API_KEY
  if (!apiUrl || !apiKey) {
    return NextResponse.json({ detail: "Server configuration error" }, { status: 500 })
  }

  const pathStr = pathSegments.join("/")
  const search = new URL(request.url).search
  const target = `${apiUrl.replace(/\/$/, "")}/${pathStr}${search}`

  const headers = new Headers()
  request.headers.forEach((value, key) => {
    const lower = key.toLowerCase()
    if (HOP_BY_HOP.has(lower)) return
    if (lower === "cookie") return
    headers.set(key, value)
  })
  headers.set("X-API-Key", apiKey)

  const method = request.method
  let body: BodyInit | undefined
  if (!["GET", "HEAD"].includes(method)) {
    body = await request.arrayBuffer()
  }

  let upstream: Response
  try {
    upstream = await fetch(target, {
      method,
      headers,
      body,
      redirect: "manual",
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : "upstream fetch failed"
    return NextResponse.json({ detail: msg }, { status: 502 })
  }

  const outHeaders = new Headers()
  upstream.headers.forEach((value, key) => {
    const lower = key.toLowerCase()
    if (lower === "transfer-encoding") return
    outHeaders.set(key, value)
  })

  const buf = await upstream.arrayBuffer()
  return new NextResponse(buf, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders,
  })
}

type RouteParams = { params: Promise<{ path: string[] }> }

export async function GET(request: NextRequest, ctx: RouteParams) {
  const { path } = await ctx.params
  return proxyRequest(request, path ?? [])
}

export async function POST(request: NextRequest, ctx: RouteParams) {
  const { path } = await ctx.params
  return proxyRequest(request, path ?? [])
}

export async function PUT(request: NextRequest, ctx: RouteParams) {
  const { path } = await ctx.params
  return proxyRequest(request, path ?? [])
}

export async function DELETE(request: NextRequest, ctx: RouteParams) {
  const { path } = await ctx.params
  return proxyRequest(request, path ?? [])
}

export async function PATCH(request: NextRequest, ctx: RouteParams) {
  const { path } = await ctx.params
  return proxyRequest(request, path ?? [])
}
