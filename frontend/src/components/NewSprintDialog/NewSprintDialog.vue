<template>
  <Dialog
    v-if="newSprint"
    v-model="showDialog"
    :options="{ title: 'New Sprint' }"
    :disableOutsideClickToClose="disableOutsideClickToClose"
  >
    <template #body-content>
      <div class="space-y-4">
        <FormControl
          label="Title"
          v-model="newSprint.doc.title"
          autocomplete="off"
          required
          ref="titleInput"
          @keydown.enter="onCreateClick"
        />

        <Autocomplete
          placeholder="Select Project"
          :options="spaceOptions"
          v-model="newSprint.doc.project"
        />

        <FormControl
          label="Sprint Goal"
          type="textarea"
          v-model="newSprint.doc.sprint_goal"
          @keydown.enter="onCreateClick"
        />

        <TextInput type="date" placeholder="Set due date" v-model="newSprint.doc.due_date" />

        <ErrorMessage class="mt-2" :message="newSprint.error" />
      </div>
    </template>

    <template #actions>
      <Button class="w-full" variant="solid" @click="onCreateClick">
        Create
      </Button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { Dialog, FormControl, Autocomplete, TextInput, ErrorMessage, Button, createResource } from 'frappe-ui'
import { showDialog, newSprint, _onSuccess } from './state'
import { useGroupedSpaceOptions } from '@/data/groupedSpaces'

const titleInput = ref<InstanceType<typeof FormControl> | null>(null)
const spaceOptions = useGroupedSpaceOptions({ filterFn: (s) => !s.archived_at })

const disableOutsideClickToClose = computed(
  () => newSprint.value?.loading || !!newSprint.value?.doc?.title
)

watch(showDialog, (val) => {
  if (val) nextTick(() => titleInput.value?.$el?.querySelector('input')?.focus())
})

// --- Generate next sprint name dynamically based on project ---
async function generateSprintName(projectId: string) {
  if (!projectId) return `new-sprint-001`

  const lastSprintResource = createResource({
    url: '/api/method/frappe.client.get_list',
    params: {
      doctype: 'Sprint',
      fields: ['title'],
      filters: [
        ['title', 'like', `${projectId}-sprint-%`],
        ['project', '=', projectId]
      ],
      order_by: 'creation desc',
      limit_page_length: 1,
    },
  })

  const response = await lastSprintResource.fetch()
  const lastTitle = response?.message?.[0]?.title || ''
  const match = lastTitle.match(/-(\d+)$/)
  const lastNumber = match ? parseInt(match[1], 10) : 0
  const nextNumber = String(lastNumber + 1).padStart(3, '0')

  return `${projectId}-sprint-${nextNumber}`
}

// --- Create Sprint ---
async function onCreateClick(e?: KeyboardEvent) {
  if (e && e instanceof KeyboardEvent && !(e.ctrlKey || e.metaKey)) return
  if (!newSprint.value?.doc.project) {
    newSprint.value.error = new Error('Project is required')
    return
  }

  // Extract project value if Autocomplete returns object
  const project = newSprint.value.doc.project
  if (project && typeof project === 'object') {
    newSprint.value.doc.project = project.value
  }

  // Auto-generate sprint name
  const sprintName = await generateSprintName(newSprint.value.doc.project)
  newSprint.value.doc.title = sprintName
  newSprint.value.doc.sprint_name = sprintName

  // Submit the doc
  newSprint.value.submit().then((doc) => {
    showDialog.value = false
    _onSuccess.value(doc)
  }).catch(err => {
    newSprint.value.error = err
  })
}
</script>
