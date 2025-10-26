// src/components/NewSprintDialog/state.ts
import { Sprint } from '@/types/doctypes'
import { useNewDoc } from 'frappe-ui/src/data-fetching'
import { ref } from 'vue'
import { useSessionUser } from '@/data/users'


// Reactive state
export const showDialog = ref(false)
export const newSprint = ref<ReturnType<typeof newDraftSprint> | null>(null)
export const _onSuccess = ref<(doc: Sprint) => void>(() => {})

// Function to open the dialog
export function showNewSprintDialog({
  defaults = {},
  onSuccess = (doc: Sprint) => {}
} = {}) {
  newSprint.value = newDraftSprint(defaults)
  console.log(newSprint)
  showDialog.value = true
  _onSuccess.value = onSuccess
}

// Factory for a new Sprint draft
function newDraftSprint(defaults: Partial<Sprint> = {}) {
  return useNewDoc<Sprint>('Sprint', {
    title: '',
    sprint_goal: '',
    status: 'Planned',
    project: '',
    ...defaults,
  })
}
