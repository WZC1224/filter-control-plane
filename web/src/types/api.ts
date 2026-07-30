export interface ApiResult<T = unknown> {
  code: number
  success: boolean
  message: string
  result: T
  timestamp: number
}

export interface LoginResult {
  token: string
  username: string
}

/** 控制平面稳定 Task 形（camelCase）。见 docs/api-contract.md */
export interface TaskItem {
  taskNo: string
  taskName: string
  taskType: string
  country: string
  status?: number
  progress?: number
  effectiveQuantity?: number
  count?: number
  createDate?: string
  description?: string
}

export interface TaskListResult {
  pageNo: number
  pageSize: number
  total: number
  data: TaskItem[]
  adapter?: string
}

export interface FilterTypeItem {
  filter_type: string
  description?: string
  min_count?: number
  max_count?: number
}

export interface CountryItem {
  countryCode?: string
  country_code?: string
  countryName?: string
  country_name?: string
}

export interface HealthResult {
  service: string
  adapter: string
  version?: string
  mock?: boolean
  /** none | agent | login | unknown — 主业务 Token */
  tokenKind?: string
  /** data818：是否配置了 DATA818_AGENT_TOKEN */
  hasAgentToken?: boolean
  /** data_center：是否配置了 DATA_CENTER_API_KEY */
  hasApiKey?: boolean
  time?: string
}

export interface BalanceResult {
  balance?: number | string
  currency?: string
  adapter?: string
}

export interface OrderItem {
  orderId: string
  userName?: string
  taskType?: string
  consumeStatus?: number
  taskCount?: string | number
  actualDeduction?: string | number
  createTime?: string
  description?: string
  thirdSource?: string
}

export interface OrderListResult {
  pageNo: number
  pageSize: number
  total: number
  data: OrderItem[]
  adapter?: string
}

export interface BillItem {
  billId: string
  username?: string
  amount?: number | string
  ledgerType?: string
  consumeType?: string
  balanceBefore?: number | string
  balanceAfter?: number | string
  bizType?: string
  bizId?: string
  description?: string
  createDate?: string
}

export interface BillListResult {
  pageNo: number
  pageSize: number
  total: number
  data: BillItem[]
  adapter?: string
}

export interface NoticeItem {
  id?: number | string
  title: string
  contentMd?: string
  bizType?: string
  level?: string
  publishStatus?: string
  createDate?: string
  expireDate?: string
}
