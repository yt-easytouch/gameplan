<template>
  <Dialog :options="{ title: 'New Task' }" :disableOutsideClickToClose="disableOutsideClickToClose"
    v-model="showDialog">
    <!-- Body -->
    <template #body-content>
      <div class="space-y-4" v-if="newTask">



        <!-- Title -->
        <FormControl label="Title" v-model="newTask.doc.title" autocomplete="off" required ref="titleInput"
          @keydown.enter="onCreateClick" />

        <!-- Project -->
        <Autocomplete placeholder="Project" :options="spaceOptions" v-model="newTask.doc.project">
          <template #prefix>
            <div class="mr-2 leading-4 font-[emoji]" v-if="newTask.doc.project">
              {{ useSpace(newTask.doc.project?.value ?? newTask.doc.project).value.icon }}
            </div>
          </template>
          <template #item-prefix="{ option }">
            <div class="leading-4 font-[emoji]">{{ option.icon }}</div>
          </template>
        </Autocomplete>

        <!-- Sprint -->
        <Autocomplete placeholder="Sprint" :options="SprintOptions" v-model="newTask.doc.sprint" />

        <!-- Description -->
        <FormControl label="Description" type="textarea" v-model="newTask.doc.description"
          @keydown.enter="onCreateClick" />

        <!-- Assigned user + Due date -->
        <div class="grid grid-cols-2 gap-2">
          <Autocomplete placeholder="Assign a user" :options="assignableUsers" v-model="newTask.doc.assigned_to" />
          <TextInput type="date" placeholder="Set due date" v-model="newTask.doc.due_date" />
        </div>




        <!-- <Dropdown class="w-full -z-30" :options="typeOptions()" :teleport="true">
          <Button class="w-full justify-start">
            <template #prefix v-if="newTask.doc.type">
              <TaskStatusIcon :type="newTask.doc.type" />
            </template>
            {{ newTask.doc.type || 'Select type' }}
          </Button>
        </Dropdown> -->


        <Dropdown 
        :options="[
          {
            label: 'Edit',
            icon: 'edit',
          },
          {
            label: 'Delete', icon: 'trash-2'

          }, {
            label: 'Edit',
            icon: 'edit',
          },
          {
            label: 'Delete', icon: 'trash-2'

          }, {
            label: 'Edit',
            icon: 'edit',
          },
          {
            label: 'Delete', icon: 'trash-2'

          }, {
            label: 'Edit',
            icon: 'edit',
          },
          {
            label: 'Delete', icon: 'trash-2'

          },
        ]"
        class="bg-red-500 z-index: 7777; "
         />


        <!-- Error message -->
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
import { ref, computed, h, watch, useTemplateRef } from 'vue'
import {
  Dialog,
  FormControl,
  Autocomplete,
  Dropdown,
  TextInput,
  ErrorMessage,
  Button,
  call,
} from 'frappe-ui'
import TaskStatusIcon from './TaskStatusIcon.vue'
import { activeUsers } from '@/data/users'
import { GPTask } from '@/types/doctypes'
import { showDialog, newTask, _onSuccess } from './state'
import { useGroupedSpaceOptions } from '@/data/groupedSpaces'
import { useSpace } from '@/data/spaces'
import KeyboardShortcut from '../KeyboardShortcut.vue'

const titleInput = useTemplateRef('titleInput')

// --- Project options
const spaceOptions = useGroupedSpaceOptions({
  filterFn: (space) => !space.archived_at,
})

// --- Sprint options (dynamic)
const SprintOptions = ref([])

async function fetchSprints(projectName?: string) {
  if (!projectName) {
    SprintOptions.value = []
    return
  }

  try {
    const res = await call('frappe.client.get_list', {
      doctype: 'Sprint',
      filters: { project: projectName },
      fields: ['name', 'title'],
    })

    SprintOptions.value = (res || []).map((sprint: any) => ({
      label: sprint.title || sprint.name,
      value: sprint.name,
    }))
  } catch (err) {
    console.error('Error fetching sprints:', err)
  }
}

// Watch for project changes
watch(
  () => newTask.value?.doc?.project,
  (project) => {
    const projectName = project?.value ?? project
    fetchSprints(projectName)
  },
  { immediate: true },
)

// --- Status options
function statusOptions() {
  return (['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled'] as GPTask['status'][]).map(
    (status) => ({
      icon: () => h(TaskStatusIcon, { status }),
      label: status,
      onClick: () => {
        if (newTask.value) newTask.value.doc.status = status
      },
    }),
  )
}

// --- Type options
function typeOptions() {
  return (['Task', 'Bug'] as GPTask['type'][]).map((type) => ({
    icon: () => h(TaskStatusIcon, { type }),
    label: type,
    onClick: () => {
      if (newTask.value) newTask.value.doc.type = type
    },
  }))
}

// --- Assignable users
const assignableUsers = computed(() =>
  activeUsers.value.map((user) => ({
    label: user.full_name,
    value: user.name,
  })),
)

// --- Create task
function onCreateClick(e: KeyboardEvent) {
  if (e instanceof KeyboardEvent && !(e.ctrlKey || e.metaKey)) return
  if (!newTask.value?.doc.title) {
    newTask.value.error = new Error('Task title is required')
    return
  }

  newTask.value.doc.assigned_to = newTask.value.doc.assigned_to?.value
  newTask.value.doc.project = newTask.value.doc.project?.value
  newTask.value.doc.sprint = newTask.value.doc.sprint?.value

  newTask.value.submit().then((doc) => {
    showDialog.value = false
    _onSuccess.value(doc)
  })
}

// --- Prevent accidental close
const disableOutsideClickToClose = computed(
  () => newTask.value?.loading || newTask.value?.doc?.title != '',
)

// --- Auto-focus on open
watch(showDialog, (val) => {
  if (val) setTimeout(() => titleInput.value.$el?.querySelector('input')?.focus(), 100)
})
</script>