import { ref, computed } from 'vue'
import { call } from 'frappe-ui'

const DiscussionOptions = ref<any[]>([])

export function useDiscussionOptions() {
  const formattedDiscussionOptions = computed(() =>
    DiscussionOptions.value.map((s) => ({
      label: s.title,
      value: s.name,
      project: s.project,
    })),
  )

  async function loadDiscussions(project?: string) {
    try {
      const res = await call('gameplan.api.get_discussions', { project })
      DiscussionOptions.value = res
    } catch (error) {
      console.error('Failed to load Discussions:', error)
    }
  }

  return {
    DiscussionOptions,
    formattedDiscussionOptions,
    loadDiscussions,
  }
}
