/**
 * Contrato alinhado ao backend (`SettingsService`, `get_category_values`):
 * chaves `ai.*`, `bot.*`, `whatsapp.*`, `notifications.*` com valor `{ v: ... }` no armazenamento.
 */

import type { SettingResponse } from "@/lib/api-client"
import { updateSetting } from "@/lib/api-client"

/** Extrai o valor escalar/objeto guardado (formato `{ v: T }` ou legado objeto plano). */
export function unwrapSettingValue(value: Record<string, unknown> | undefined): unknown {
  if (!value || typeof value !== "object") return undefined
  if ("v" in value && Object.prototype.hasOwnProperty.call(value, "v")) {
    return value.v
  }
  return value
}

/** Corpo PUT esperado pelo backend para um único campo escalar ou objeto JSON. */
export function wrapScalarForPut(v: unknown): Record<string, unknown> {
  return { v }
}

export async function putScalarKey(key: string, v: unknown): Promise<void> {
  await updateSetting(key, wrapScalarForPut(v))
}

/** Índice por chave a partir da lista GET /settings/{category}. */
export function indexByKey(rows: SettingResponse[]): Map<string, Record<string, unknown>> {
  return new Map(rows.map((r) => [r.key, r.value]))
}
