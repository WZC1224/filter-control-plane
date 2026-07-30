import { ElMessage } from 'element-plus'

/** 复制文本到剪贴板；失败时提示。 */
export async function copyText(text: string, okMsg = '已复制'): Promise<boolean> {
  const v = (text || '').trim()
  if (!v || v === '-') {
    ElMessage.warning('无可复制内容')
    return false
  }
  try {
    await navigator.clipboard.writeText(v)
    ElMessage.success(okMsg)
    return true
  } catch {
    ElMessage.error('复制失败')
    return false
  }
}
