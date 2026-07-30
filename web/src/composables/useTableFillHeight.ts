import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

/** 让 el-table 高度贴合父级 `.table-scroll--fill`，表内滚动、不撑破底边。 */
export function useTableFillHeight(min = 180) {
  const tableWrap = ref<HTMLElement | null>(null)
  const tableHeight = ref(min)
  let ro: ResizeObserver | undefined

  function measure() {
    const el = tableWrap.value
    if (!el) return
    const h = Math.floor(el.clientHeight)
    if (h > 0) tableHeight.value = Math.max(min, h)
  }

  function disconnect() {
    ro?.disconnect()
    ro = undefined
  }

  function connect(el: HTMLElement) {
    disconnect()
    measure()
    if (typeof ResizeObserver === 'undefined') return
    ro = new ResizeObserver(() => measure())
    ro.observe(el)
  }

  onMounted(() => {
    nextTick(() => {
      if (tableWrap.value) connect(tableWrap.value)
    })
  })

  watch(tableWrap, (el) => {
    if (el) nextTick(() => connect(el))
    else disconnect()
  })

  onUnmounted(disconnect)

  return { tableWrap, tableHeight, measureTable: measure }
}
