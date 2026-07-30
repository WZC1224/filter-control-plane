import { request } from './http'
import type { OrderListResult } from '@/types/api'

export function listOrdersApi(params?: Record<string, string | number | undefined>) {
  return request<OrderListResult>({
    url: '/orders',
    method: 'get',
    params,
  })
}
