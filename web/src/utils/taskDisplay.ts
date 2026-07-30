import type { CountryItem, TaskItem } from '@/types/api'

export type DownloadFormat = 'csv' | 'txt' | 'xlsx' | 'invalid'

export const DOWNLOAD_FORMATS: { value: DownloadFormat; label: string }[] = [
  { value: 'csv', label: 'CSV' },
  { value: 'txt', label: '有效 TXT' },
  { value: 'xlsx', label: 'XLSX' },
  { value: 'invalid', label: '无效 TXT' },
]

export function countryCode(item: CountryItem) {
  return item.countryCode || item.country_code || ''
}

export function countryName(item: CountryItem) {
  return item.countryName || item.country_name || countryCode(item)
}

export function taskNo(row: TaskItem) {
  return row.taskNo || '-'
}

export function statusText(status?: number) {
  const map: Record<number, string> = {
    [-1]: '失败',
    0: '排队',
    1: '完成',
    2: '进行中',
    3: '关闭',
  }
  return status === undefined ? '-' : map[status] ?? String(status)
}

export function statusType(status?: number): 'info' | 'success' | 'warning' | 'danger' {
  if (status === 1) return 'success'
  if (status === 2) return 'warning'
  if (status === -1 || status === 3) return 'danger'
  return 'info'
}

export function isActiveStatus(status?: number) {
  return status === 0 || status === 2
}
