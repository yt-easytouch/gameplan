import { ref, computed } from 'vue'
import { call } from 'frappe-ui'

const sprintOptions = ref<any[]>([])

export function useSprintOptions() {
  const formattedSprintOptions = computed(() =>
    sprintOptions.value.map((s) => ({
      label: s.title,
      value: s.name,
      project: s.project,
    })),
  )

  async function loadSprints(project?: string) {
    try {
      const res = await call('gameplan.api.get_sprints', { project })
      sprintOptions.value = res
    } catch (error) {
      console.error('Failed to load sprints:', error)
    }
  }

  return {
    sprintOptions,
    formattedSprintOptions,
    loadSprints,
  }
}
