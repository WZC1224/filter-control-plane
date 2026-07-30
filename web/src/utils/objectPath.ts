import { ElMessage, ElMessageBox } from 'element-plus'

/** 下游仅返回 OSS path 时：展示并可复制。 */
export async function promptObjectPath(path: string): Promise<void> {
  try {
    await ElMessageBox.confirm(path, '剩余号已生成（OSS 路径）', {
      confirmButtonText: '复制路径',
      cancelButtonText: '关闭',
      type: 'warning',
      distinguishCancelAndClose: true,
      customClass: 'object-path-box',
    })
  } catch {
    return
  }
  try {
    await navigator.clipboard.writeText(path)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动选中路径')
  }
}
