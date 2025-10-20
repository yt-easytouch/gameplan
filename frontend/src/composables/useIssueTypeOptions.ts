import { ref, computed, onMounted } from 'vue'
import { call } from 'frappe-ui'

const issueTypeOptions = ref<any[]>([])
const loaded = ref(false)

export function useIssueTypeOptions() {
  const formattedIssueTypeOptions = computed(() =>
    issueTypeOptions.value.map((i) => ({
      label: i.type || i.name,
      value: i.name,
    })),
  )

  async function loadIssueTypes() {
    // prevent multiple network calls if already loaded
    if (loaded.value) return
    loaded.value = true

    try {
      const res = await call('gameplan.api.get_issue_type', {})
      issueTypeOptions.value = res
    } catch (error) {
      console.error('Failed to load issue types:', error)
    }
  }

  // automatically load on first use
  onMounted(() => loadIssueTypes())

  return {
    issueTypeOptions,
    formattedIssueTypeOptions,
    loadIssueTypes,
  }
}
