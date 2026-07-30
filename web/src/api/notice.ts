import { request } from './http'
import type { BillListResult, NoticeItem } from '@/types/api'

export function listBillsApi(params?: Record<string, string | number | undefined>) {
  return request<BillListResult>({
    url: '/bills',
    method: 'get',
    params,
  })
}

export function listNoticesApi() {
  return request<NoticeItem[]>({
    url: '/notices',
    method: 'get',
  })
}

export function getNoticeApi(noticeId: string | number) {
  return request<NoticeItem>({
    url: `/notices/${encodeURIComponent(String(noticeId))}`,
    method: 'get',
  })
}
