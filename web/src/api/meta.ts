import { request } from './http'
import type { CountryItem, FilterTypeItem, HealthResult } from '@/types/api'

export interface BalanceResult {
  balance?: number | string
  currency?: string
  adapter?: string
  [key: string]: unknown
}

export function healthApi() {
  return request<HealthResult>({
    url: '/meta/health',
    method: 'get',
  })
}

export function filterTypesApi() {
  return request<FilterTypeItem[]>({
    url: '/meta/filter-types',
    method: 'get',
  })
}

export function countriesApi() {
  return request<CountryItem[]>({
    url: '/meta/countries',
    method: 'get',
  })
}

export function balanceApi() {
  return request<BalanceResult>({
    url: '/meta/balance',
    method: 'get',
  })
}

export interface StatDay {
  date: string
  total: number
  items?: { taskType?: string; taskNumber?: number; taskName?: string }[]
}

export interface StatisticsResult {
  days?: number
  series?: StatDay[]
  raw?: unknown
  adapter?: string
}

export function statisticsApi(taskType?: string) {
  return request<StatisticsResult>({
    url: '/meta/statistics',
    method: 'get',
    params: taskType ? { taskType } : undefined,
  })
}

export interface ThirdBalanceItem {
  thirdSourceName?: string
  balance?: number | string
}

export function thirdBalancesApi() {
  return request<ThirdBalanceItem[]>({
    url: '/meta/third-balances',
    method: 'get',
  })
}

export interface ProductItem {
  taskType: string
  name?: string
  price?: number | string
  applicationType?: string
  businessType?: string
  minCount?: number
  maxCount?: number
  thirdSource?: string
  description?: string
}

export function productsApi() {
  return request<ProductItem[]>({
    url: '/meta/products',
    method: 'get',
  })
}

export interface OrderTaskTypeItem {
  taskType: string
  description?: string
}

export function orderTaskTypesApi() {
  return request<OrderTaskTypeItem[]>({
    url: '/meta/order-task-types',
    method: 'get',
  })
}

export interface LedgerTypeItem {
  ledgerType: string
  description?: string
}

export function ledgerTypesApi() {
  return request<LedgerTypeItem[]>({
    url: '/meta/ledger-types',
    method: 'get',
  })
}

export interface DownstreamSecretInfo {
  configured: boolean
  masked: string
  kind: string
  exp?: string | null
  source: 'file' | 'env'
}

export interface DownstreamSecretsResult {
  data818Token: DownstreamSecretInfo
  data818AgentToken: DownstreamSecretInfo
  filePath: string
  adapter: string
}

export function downstreamSecretsApi() {
  return request<DownstreamSecretsResult>({
    url: '/meta/downstream-secrets',
    method: 'get',
  })
}

export function putDownstreamSecretsApi(body: {
  data818Token?: string
  data818AgentToken?: string
}) {
  return request<DownstreamSecretsResult>({
    url: '/meta/downstream-secrets',
    method: 'put',
    data: body,
  })
}
