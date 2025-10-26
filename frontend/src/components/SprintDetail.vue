<template>
  <div class="flex h-full flex-1" v-if="sprint.doc">
    <div class="w-full flex-1">
      <div class="relative p-6">
        <!-- Saving indicator -->
        <div class="absolute right-0 top-0 p-6" v-show="sprint.setValue.loading">
          <LoadingText v-if="!sprint.setValue.error" text="Saving..." />
          <ErrorMessage :message="sprint.setValue.error" />
        </div>

        <!-- Title + More Options -->
        <div class="mb-2 flex items-center justify-between space-x-2">
          <input
            type="text"
            placeholder="Sprint Title"
            class="-ml-0.5 w-full rounded-sm border-none p-0.5 text-2xl bg-surface-white font-semibold text-ink-gray-8 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
            v-model="sprint.doc.title"
            @blur="updateTitle"
            v-focus
          />
          <DropdownMoreOptions
            placement="right"
            :options="[
              {
                label: 'Delete',
                onClick: deleteSprint
              }
            ]"
          />
        </div>

        <!-- Sprint Goal -->
        <TextEditor
          ref="goalEditor"
          editor-class="prose-sm max-w-none focus-within:ring-2 focus-within:ring-outline-gray-3 rounded-sm p-0.5 -ml-0.5 min-h-[4rem]"
          placeholder="Sprint Goal"
          :content="sprint.doc.sprint_goal"
          :bubbleMenu="true"
          :floatingMenu="true"
          @blur="updateGoal"
        />

        <!-- Sprint Metadata -->
        <div class="mt-6 flex flex-wrap items-center gap-2 sm:hidden">
          <Autocomplete
            placeholder="Select Space"
            :options="spaceOptions"
            :modelValue="sprint.doc.project"
            @update:modelValue="changeSpace"
          />

          <DatePicker
            v-model="sprint.doc.start_date"
            variant="subtle"
            placeholder="Start Date"
            @update:modelValue="updateDates"
          />

          <DatePicker
            v-model="sprint.doc.end_date"
            variant="subtle"
            placeholder="End Date"
            @update:modelValue="updateDates"
          />
        </div>

        <!-- Sub-Tasks -->
        <div v-if="sprint.doc.sub_tasks?.length" class="mt-8">
          <div v-for="(sub, index) in sprint.doc.sub_tasks" :key="sub.name" class="flex items-center justify-between mb-2">
            <input
              type="text"
              v-model="sub.title"
              class="flex-1 rounded-sm border p-1"
              @blur="saveSubTasks"
            />
            <button @click="removeSubTask(index)" class="ml-2 text-red-600">Delete</button>
          </div>
          <button class="mt-2 text-blue-600" @click="addSubTask">+ Add Sub-Task</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import TextEditor from '@/components/TextEditor.vue'
import DropdownMoreOptions from './DropdownMoreOptions.vue'
import { Autocomplete, DatePicker, LoadingText, ErrorMessage, toast } from 'frappe-ui'
import { vFocus } from '@/directives'
import { useSprint } from '@/data/sprints'
import { useGroupedSpaceOptions } from '@/data/groupedSpaces'

const props = defineProps<{ sprintId: string }>()
const router = useRouter()
const sprint = useSprint(() => props.sprintId)

// Refs
const goalEditor = ref<InstanceType<typeof TextEditor> | null>(null)
const spaceOptions = useGroupedSpaceOptions({ filterFn: s => !s.archived_at })

// --- Update Handlers ---
function updateTitle() {
  if (!sprint.doc) return
  sprint.setValue.submit({ title: sprint.doc.title })
}

function updateGoal() {
  if (!sprint.doc || !goalEditor.value?.editor) return
  const html = goalEditor.value.editor.getHTML()
  sprint.setValue.submit({ sprint_goal: html })
}

function updateDates() {
  if (!sprint.doc) return
  sprint.setValue.submit({
    start_date: sprint.doc.start_date,
    end_date: sprint.doc.end_date,
  })
}

function changeSpace(option: { value: string } | null) {
  if (!sprint.doc) return
  sprint.doc.project = option?.value || ''
  sprint.setValue.submit({ project: sprint.doc.project }).then(() => {
    router.replace({ name: sprint.doc.project ? 'SpaceSprint' : 'Sprint', params: { sprintId: sprint.doc.name, spaceId: sprint.doc.project }})
  })
}

// --- Sub Task Management ---
function addSubTask() {
  if (!sprint.doc.sub_tasks) sprint.doc.sub_tasks = []
  sprint.doc.sub_tasks.push({ title: '', name: `sub-${Date.now()}` })
  saveSubTasks()
}

function removeSubTask(index: number) {
  sprint.doc.sub_tasks?.splice(index, 1)
  saveSubTasks()
}

function saveSubTasks() {
  sprint.setValue.submit({ sub_tasks: sprint.doc.sub_tasks || [] })
}

// --- Delete Sprint ---
function deleteSprint() {
  $dialog({
    title: 'Delete Sprint',
    message: 'Are you sure you want to delete this sprint?',
    actions: [
      {
        label: 'Delete',
        theme: 'red',
        variant: 'solid',
        onClick({ close }) {
          sprint.delete.submit().then(() => {
            close()
            router.back()
            toast.success('Sprint deleted!')
          })
        },
      },
    ],
  })
}
</script>



