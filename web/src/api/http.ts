import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResult } from '@/types/api'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const http: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 60000,
})

http.interceptors.request.use((config) => {
  const user = useUserStore()
  if (user.token) {
    config.headers.Authorization = `Bearer ${user.token}`
  }
  return config
})

http.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.config.responseType === 'blob') {
      return response
    }
    const data = response.data as ApiResult
    if (!data?.success) {
      if (data?.code === 401) {
        const user = useUserStore()
        user.logout()
        router.replace({ name: 'login' })
      }
      ElMessage.error(data?.message || '请求失败')
      return Promise.reject(data)
    }
    return response
  },
  (error) => {
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  },
)

export async function request<T>(config: Parameters<typeof http.request>[0]): Promise<T> {
  const res = await http.request<ApiResult<T>>(config)
  return res.data.result
}

function filenameFromDisposition(header: string | undefined, fallback: string): string {
  if (!header) return fallback
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(header)
  if (utf8?.[1]) {
    try {
      return decodeURIComponent(utf8[1])
    } catch {
      return utf8[1]
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(header)
  return plain?.[1] || fallback
}

/** 下载文件流；若后端返回 JSON 错误 envelope，解析并抛出。 */
export async function downloadBlob(
  url: string,
  params?: Record<string, string>,
  fallbackName = 'download.bin',
): Promise<void> {
  const res = await http.get(url, { params, responseType: 'blob' })
  const contentType = String(res.headers['content-type'] || '')
  const blob = res.data as Blob
  if (contentType.includes('application/json')) {
    const text = await blob.text()
    let data: ApiResult
    try {
      data = JSON.parse(text) as ApiResult
    } catch {
      ElMessage.error('下载失败')
      return Promise.reject(new Error('invalid json error body'))
    }
    if (data.code === 401) {
      const user = useUserStore()
      user.logout()
      router.replace({ name: 'login' })
    }
    ElMessage.error(data.message || '下载失败')
    return Promise.reject(data)
  }
  const name = filenameFromDisposition(res.headers['content-disposition'], fallbackName)
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = name
  a.click()
  URL.revokeObjectURL(objectUrl)
}

export default http
