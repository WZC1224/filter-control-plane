import { ElMessage } from 'element-plus'
import http, { request, downloadBlob } from './http'
import type { ApiResult, TaskListResult } from '@/types/api'
import type { DownloadFormat } from '@/utils/taskDisplay'

export function listTasksApi(params?: Record<string, string | number | undefined>) {
  return request<TaskListResult>({
    url: '/tasks',
    method: 'get',
    params,
  })
}

export function createTaskApi(form: FormData) {
  return request<Record<string, unknown>>({
    url: '/tasks',
    method: 'post',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function queryTaskApi(taskNo: string) {
  return request<Record<string, unknown>>({
    url: `/tasks/${encodeURIComponent(taskNo)}`,
    method: 'get',
  })
}

export function downloadTaskApi(taskNo: string, format: DownloadFormat = 'csv') {
  return downloadBlob(
    `/tasks/${encodeURIComponent(taskNo)}/download`,
    { format },
    `${taskNo}.${format}`,
  )
}

export function closeTaskApi(taskNo: string) {
  return request<Record<string, unknown>>({
    url: `/tasks/${encodeURIComponent(taskNo)}/close`,
    method: 'post',
  })
}

export function refundTaskApi(taskNo: string) {
  return request<Record<string, unknown>>({
    url: `/tasks/${encodeURIComponent(taskNo)}/refund`,
    method: 'post',
  })
}

export function retryTaskApi(taskNo: string) {
  return request<Record<string, unknown>>({
    url: `/tasks/${encodeURIComponent(taskNo)}/retry`,
    method: 'post',
  })
}

/** 导出剩余号：文件流；或 JSON {objectPath, downloadable:false}（调用方处理路径提示） */
export async function exportRemainingApi(taskNo: string): Promise<{ objectPath?: string } | void> {
  const res = await http.get(`/tasks/${encodeURIComponent(taskNo)}/export-remaining`, {
    responseType: 'blob',
  })
  const contentType = String(res.headers['content-type'] || '')
  const blob = res.data as Blob
  if (contentType.includes('application/json')) {
    const text = await blob.text()
    let data: ApiResult<{ objectPath?: string; downloadable?: boolean }>
    try {
      data = JSON.parse(text) as ApiResult<{ objectPath?: string; downloadable?: boolean }>
    } catch {
      ElMessage.error('导出失败')
      return Promise.reject(new Error('invalid json'))
    }
    if (!data.success) {
      ElMessage.error(data.message || '导出失败')
      return Promise.reject(data)
    }
    if (data.result?.objectPath) {
      return { objectPath: data.result.objectPath }
    }
    return
  }
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = `${taskNo}-remaining.txt`
  a.click()
  URL.revokeObjectURL(objectUrl)
}
