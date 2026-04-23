"use client"

import { useEffect, useState } from "react"

import { fetchUnreadCount } from "@/lib/api-client"

const POLL_MS = 30_000

/**
 * Contagem de conversas não lidas (`read == false` no backend).
 * `null` antes do primeiro fetch bem-sucedido ou após erro.
 */
export function useUnreadCount(): number | null {
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const n = await fetchUnreadCount()
        if (!cancelled) setCount(n)
      } catch {
        if (!cancelled) setCount(null)
      }
    }

    void load()
    const id = window.setInterval(() => void load(), POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  return count
}
