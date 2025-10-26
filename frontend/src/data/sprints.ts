import { watch, computed, MaybeRefOrGetter, toValue } from 'vue'
import { useDoc } from 'frappe-ui/src/data-fetching'
import type { Sprint } from '@/types/doctypes'

const sprintsCache: Record<string, ReturnType<typeof useDoc>> = {}

export function useSprint(sprintId: MaybeRefOrGetter<string>) {
  interface Sprintk extends Sprint {}
  interface SprintkMethods {
    trackVisit: () => void
  }

  const idRef = computed(() => toValue(sprintId))

  const getOrCreateDoc = (id: string) => {
    if (!sprintsCache[id]) {
      sprintsCache[id] = useDoc<Sprintk, SprintkMethods>({
        doctype: 'Sprint',
        name: id,
        methods: {
          trackVisit: 'track_visit',
        },
      })
    }
    return sprintsCache[id]
  }

  let sprintDoc = getOrCreateDoc(idRef.value)

  // 👇 This ensures when the route param changes, you fetch the right one
  watch(idRef, (newId) => {
    sprintDoc = getOrCreateDoc(newId)
  })

  return sprintDoc
}
