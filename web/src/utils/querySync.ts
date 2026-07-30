import type { LocationQuery, LocationQueryRaw } from 'vue-router'

/** 从 route.query 取字符串；空则 fallback。 */
export function qStr(query: LocationQuery, key: string, fallback = ''): string {
  const v = query[key]
  const s = Array.isArray(v) ? v[0] : v
  return s == null || s === '' ? fallback : String(s)
}

/** 从 route.query 取正整数。 */
export function qInt(query: LocationQuery, key: string, fallback: number): number {
  const n = Number(qStr(query, key, ''))
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : fallback
}

/** 可选状态码（含 0 / -1）。 */
export function qStatus(query: LocationQuery, key: string): number | undefined {
  const raw = qStr(query, key, '')
  if (raw === '') return undefined
  const n = Number(raw)
  return Number.isFinite(n) ? n : undefined
}

/** 去掉空值，生成 LocationQueryRaw。 */
export function compactQuery(parts: Record<string, string | number | undefined | null>): LocationQueryRaw {
  const out: LocationQueryRaw = {}
  for (const [k, v] of Object.entries(parts)) {
    if (v === undefined || v === null || v === '') continue
    out[k] = String(v)
  }
  return out
}
