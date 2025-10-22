<template>
  <Dialog
    :options="{ title: 'New Task' }"
    :disableOutsideClickToClose="disableOutsideClickToClose"
    v-model="showDialog"
  >
    <!-- Body -->
    <template #body-content>
      <div class="space-y-4" v-if="newTask">
        <!-- 🏷 Title -->
        <FormControl
          label="Title"
          v-model="newTask.doc.title"
          autocomplete="off"
          required
          ref="titleInput"
          @keydown.enter="onCreateClick"
        />

        <!-- 🧩 Project -->
       <Autocomplete
          placeholder="Select Project"
          :options="spaceOptions"
          v-model="newTask.doc.project"
          :disabled="!newTask.doc.is_saved" <!-- Optional: disable until saved -->
        >
          <template #prefix>
            <div
              class="mr-2 leading-4 font-[emoji]"
              v-if="newTask.doc.project && !isNewTask"
            >
              {{ useSpace(newTask.doc.project?.value ?? newTask.doc.project).value.icon }}
            </div>
          </template>

          <template #item-prefix="{ option }">
            <div class="leading-4 font-[emoji]">{{ option.icon }}</div>
          </template>
        </Autocomplete>


        <!-- 🧩 Sprint (filtered by project) -->
        <Autocomplete
          placeholder="Sprint"
          :options="formattedSprintOptions"
          v-model="newTask.doc.sprint"
        /> 
        <!-- 🧩 GP Discussion (filtered by project) -->
        <Autocomplete
          placeholder="Discussion"
          :options="formattedDiscussionOptions"
          v-model="newTask.doc.gp_discussion"
        />

        <!-- 📝 Description -->
        <FormControl
          label="Description"
          type="textarea"
          v-model="newTask.doc.description"
          @keydown.enter="onCreateClick"
        />

        <!-- 👤 Assigned user + ⏰ Due date -->
        <div class="grid grid-cols-2 gap-2">
          <Autocomplete
            placeholder="Assign a user"
            :options="assignableUsers"
            v-model="newTask.doc.assigned_to"
          />
          <TextInput
            type="date"
            placeholder="Set due date"
            v-model="newTask.doc.due_date"
          />
        </div>

        <ErrorMessage class="mt-2" :message="newTask.error" />
      </div>
    </template>

    <!-- Actions -->
    <template #actions>
      <Button class="w-full relative" variant="solid" @click="onCreateClick">
        Create
        <div class="absolute right-0 top-0 h-7 pr-2 flex items-center justify-center">
          <KeyboardShortcut ctrl> Enter </KeyboardShortcut>
        </div>
      </Button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, useTemplateRef } from 'vue'
import {
  Dialog,
  FormControl,
  Autocomplete,
  TextInput,
  ErrorMessage,
  Button,
} from 'frappe-ui'
import { activeUsers } from '@/data/users'
import { useGroupedSpaceOptions } from '@/data/groupedSpaces'
import { useSpace } from '@/data/spaces'
import KeyboardShortcut from '../KeyboardShortcut.vue'
import { showDialog, newTask, _onSuccess } from './state'
import { useSprintOptions } from '@/composables/useSprintOptions'
import { useDiscussionOptions } from '@/composables/useDiscussionOptions'

// --- Refs
const titleInput = useTemplateRef('titleInput')

// --- Project options
const spaceOptions = useGroupedSpaceOptions({
  filterFn: (space) => !space.archived_at,
})

// --- Sprint options (reactive to project)
const { formattedSprintOptions, loadSprints } = useSprintOptions()
const { formattedDiscussionOptions, loadDiscussions } = useDiscussionOptions()

watch(
  () => newTask.value?.doc.project,
  async (project) => {
    if (project?.value || project) {
      await loadSprints(project.value || project)
      await loadDiscussions(project.value || project)
    }
  },
  { immediate: true }
)

// --- Assignable users
const assignableUsers = computed(() =>
  activeUsers.value.map((user) => ({
    label: user.full_name,
    value: user.name,
  })),
)

// --- Create handler
function onCreateClick(e: KeyboardEvent) {
  if (e instanceof KeyboardEvent && !(e.ctrlKey || e.metaKey)) return
  if (!newTask.value?.doc.title) {
    newTask.value.error = new Error('Task title is required')
    return
  }

  newTask.value.doc.assigned_to = newTask.value.doc.assigned_to?.value
  newTask.value.doc.project = newTask.value.doc.project?.value
  newTask.value.doc.sprint = newTask.value.doc.sprint?.value
  newTask.value.doc.gp_discussion = newTask.value.doc.gp_discussion?.value

  newTask.value.submit().then((doc) => {
    showDialog.value = false
    _onSuccess.value(doc)
  })
}

// --- Prevent accidental close
const disableOutsideClickToClose = computed(
  () => newTask.value?.loading || newTask.value?.doc?.title != '',
)

// --- Auto-focus title
watch(showDialog, (val) => {
  if (val)
    setTimeout(() => titleInput.value.$el?.querySelector('input')?.focus(), 100)
})
</script>
