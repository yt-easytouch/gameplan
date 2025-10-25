<template>
  <div class="flex h-full flex-1" v-if="task.doc">
    <!-- 🧩 Main Task Area -->
    <div class="w-full flex-1">
      <div class="relative p-6">
        <!-- 💾 Saving indicator -->
        <div class="absolute right-0 top-0 p-6" v-show="task.setValue.loading">
          <LoadingText v-if="!task.setValue.error" text="Saving..." />
          <ErrorMessage :message="task.setValue.error" />
        </div>

        <!-- 📝 Title + More -->
        <div class="mb-2 flex items-center justify-between space-x-2">
          <input
            type="text"
            placeholder="Title"
            class="-ml-0.5 w-full rounded-sm border-none p-0.5 text-2xl bg-surface-white font-semibold text-ink-gray-8 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
            v-model="task.doc.title"
            @blur="task.setValue.submit({ title: task.doc.title })"
            v-focus
          />
          <DropdownMoreOptions
            placement="right"
            :options="[
              {
                label: 'Delete',
                onClick: () => {
                  $dialog({
                    title: 'Delete task',
                    message: 'Are you sure you want to delete this task?',
                    actions: [
                      {
                        label: 'Delete',
                        theme: 'red',
                        variant: 'solid',
                        onClick({ close }) {
                          return task.delete.submit().then(() => {
                            close()
                            $router.back()
                          })
                        },
                      },
                    ],
                  })
                },
              },
            ]"
          />
        </div>

        <!-- 🧠 Description -->
        <TextEditor
          ref="description"
          editor-class="prose-sm max-w-none focus-within:ring-2 focus-within:ring-outline-gray-3 rounded-sm p-0.5 -ml-0.5 min-h-[4rem]"
          placeholder="Description"
          :content="task.doc.description"
          :bubbleMenu="true"
          :floatingMenu="true"
          @blur="
            !$refs.description.editor.isEmpty
              ? task.setValue.submit({
                  description: $refs.description.editor.getHTML(),
                })
              : null
          "
        />

        <!-- 📱 Mobile Compact Fields -->
        <div class="mt-8 flex flex-wrap items-center gap-2 sm:hidden">
          <Autocomplete
            placeholder="Assign a user"
            :options="assignableUsers"
            v-model="task.doc.assigned_to"
            @update:modelValue="changeAssignee"
          />

          <DatePicker
            v-model="task.doc.due_date"
            variant="subtle"
            placeholder="Due date"
            @update:modelValue="(v) => task.setValue.submit({ due_date: v })"
          />

          <Dropdown :options="statusOptions">
            <Button>
              <template #prefix>
                <TaskStatusIcon :status="task.doc.status" />
              </template>
              {{ task.doc.status || 'Set status' }}
            </Button>
          </Dropdown>

          <Dropdown :options="priorityOptions">
            <Button>
              <template v-if="task.doc.priority" #prefix>
                <TaskPriorityIcon :priority="task.doc.priority" />
              </template>
              {{ task.doc.priority || 'Set priority' }}
            </Button>
          </Dropdown>

          <Autocomplete
            placeholder="Select space"
            :options="spaceOptions"
            :modelValue="task.doc.project"
            @update:modelValue="changeSpace"
          />
        </div>

      <!-- 📋 Sub Tasks -->
<div class="mt-10 border-t border-gray-200 pt-6">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-ink-gray-8 flex items-center gap-2">
      <FeatherIcon name="check-square" class="w-5 h-5 text-primary" />
      Sub Tasks
    </h3>
  </div>

  <!-- Table -->
  <div class="overflow-x-auto rounded-lg border border-gray-200 bg-surface-white shadow-sm">
    <table class="min-w-full text-base text-left text-ink-gray-8">
      <thead class="bg-gray-50 text-ink-gray-6 font-medium">
        <tr>
          <th class="px-4 py-2 w-[20%]">Title</th>
          <th class="px-4 py-2 w-[20%]">Collaborators</th>
          <th class="px-4 py-2 w-[15%]">Status</th>
          <th class="px-4 py-2 w-[15%]">Due Date</th>
          <th class="px-4 py-2 text-right w-[10%]">Actions</th>
        </tr>
      </thead>

      <TransitionGroup tag="tbody" name="fade">
        <tr
          v-for="(sub, index) in task.doc.sub_tasks || []"
          :key="sub.name || index"
          class="border-t border-gray-10 hover:bg-gray-40 transition-colors duration-150"
        >
          <!-- Title -->
          <td class="px-4 py-2">
            <input
              type="text"
              v-model="sub.title"
              placeholder="Sub task title"
              class="w-full border-none bg-transparent text-ink-gray-8 placeholder-ink-gray-4 
                     focus:ring-2 focus:ring-outline-gray-3 rounded-md px-2 py-1 text-base font-medium"
              @blur="saveSubTasks"
            />
          </td>

          <!-- Assigned User -->
          <td class="px-4 py-2">
           
          <Autocomplete
            placeholder="Select collaborators"
            :options="assignableUsers"
            :modelValue="sub.sub_task_collaborate?.map(m => m.user) || []"
            multiple
            class="text-sm w-full"
            @update:modelValue="(selected) => handleCollaboratorChange(sub, selected)"
          />


          </td>

          <!-- Status -->
          <td class="px-4 py-2">
            <Dropdown
              :options="['Backlog', 'Todo', 'In Progress', 'Done'].map(s => ({
                label: s,
                onClick: () => {
                  sub.status = s
                  saveSubTasks(task.doc.sub_tasks)
                }
              }))"
            >
              <div
                class="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full cursor-pointer w-fit transition-all"
                :class="statusBadgeClass(sub.status)"
              >
                <span class="w-2 h-2 rounded-full" :class="statusDotClass(sub.status)"></span>
                {{ sub.status || 'Status' }}
              </div>
            </Dropdown>
          </td>

          <!-- Due Date -->
          <td class="px-4 py-2">
            <DatePicker
              v-model="sub.due_date"
              placeholder="Due date"
              size="sm"
              @update:modelValue="saveSubTasks(task.doc.sub_tasks)"
            />
          </td>

          <!-- Delete -->
          <td class="px-4 py-2 text-right">
            <Button
              size="icon"
              variant="ghost"
              class="text-red-500 hover:bg-red-100 rounded-full"
              @click="removeSubTask(index)"
            >
              <FeatherIcon name="trash-2" class="w-4 h-4" />
            </Button>
          </td>
        </tr>
      </TransitionGroup>

      <!-- Empty State -->
      <tr v-if="!task.doc.sub_tasks?.length">
        <td colspan="6" class="py-6 text-center text-ink-gray-5 text-base">
          <FeatherIcon name="clipboard" class="w-5 h-5 inline mb-1 text-gray-400" />
          <p>No sub tasks yet — add one below.</p>
        </td>
      </tr>
    </table>
  </div>

  <!-- Add Sub Task Button -->
  <div class="flex justify-start mt-4">
    <Button
      variant="ghost"
      size="sm"
      class="flex items-center gap-1.5 text-primary hover:bg-primary/10 font-medium px-2 py-1.5"
      @click="addSubTask"
    >
      <FeatherIcon name="plus-circle" class="w-4 h-4" />
      <span>Add Sub Task</span>
    </Button>
  </div>
</div>












        <!-- 💬 Comments -->
        <CommentsList class="mt-8" doctype="GP Task" :name="taskId" />
      </div>
    </div>

    <!-- 📋 Sidebar -->
    <div class="hidden w-[20rem] shrink-0 border-l sm:block">
      <div class="grid grid-cols-2 items-center gap-y-6 p-6 text-base text-ink-gray-6">
        <!-- Task ID -->
        <div>Development</div>
        <div>
          <TextInput type="text" v-model="task.doc.taskid" readonly>
            <template #suffix>
              <FeatherIcon class="w-4 cursor-pointer" name="copy" @click="copyTaskId" />
            </template>
          </TextInput>
        </div>

        <!-- Assignee -->
        <div>Assignee</div>
        <div>
          <Autocomplete
            placeholder="Assign a user"
            :options="assignableUsers"
            v-model="task.doc.assigned_to"
            @update:modelValue="changeAssignee"
          />
        </div>

        <!-- Due Date -->
        <div>Due Date</div>
        <div>
          <DatePicker
            v-model="task.doc.due_date"
            variant="subtle"
            placeholder="Due date"
            @update:modelValue="(v) => task.setValue.submit({ due_date: v })"
          />
        </div>

        <!-- Space -->
        <div>Space</div>
        <div>
          <Autocomplete
            placeholder="Select space"
            :options="spaceOptions"
            :modelValue="selectedSpace"
            @update:modelValue="changeSpace"
          />
        </div>

        <!-- Discussion -->
        <div>Discussion</div>
        <div>
          <Autocomplete
            placeholder="Discussion"
            :options="formattedDiscussionOptions"
            v-model="task.doc.gp_discussion"
            @update:modelValue="changeDiscussion"
          />
        </div>

        <!-- Sprint -->
        <div>Sprint</div>
        <div>
          <Autocomplete
            placeholder="Sprint"
            :options="formattedSprintOptions"
            v-model="task.doc.sprint"
            @update:modelValue="changeSprint"
          />
        </div>

        <!-- Members -->
        <div>Collaborators</div>
        <div>
          <Autocomplete
            :options="assignableUsers"
            :modelValue="task.doc.task_collaborate?.map((m) => m.user) || []"
            @update:modelValue="changeMembers"
            multiple
          />
        </div>

        <!-- Status -->
        <div>Status</div>
        <div>
          <Dropdown :options="statusOptions">
            <Button>
              <template #prefix>
                <TaskStatusIcon :status="task.doc.status" />
              </template>
              {{ task.doc.status || 'Set status' }}
            </Button>
          </Dropdown>
        </div>

        <!-- Priority -->
        <div>Priority</div>
        <div>
          <Dropdown :options="priorityOptions">
            <Button>
              <template v-if="task.doc.priority" #prefix>
                <TaskPriorityIcon :priority="task.doc.priority" />
              </template>
              {{ task.doc.priority || 'Set priority' }}
            </Button>
          </Dropdown>
        </div>
      </div>
    </div>
  </div>
</template>




<script setup lang="ts">
import { h, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import TextEditor from '@/components/TextEditor.vue'
import CommentsList from '@/components/CommentsList.vue'
import TaskStatusIcon from '@/components/NewTaskDialog/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/icons/TaskPriorityIcon.vue'
import DropdownMoreOptions from './DropdownMoreOptions.vue'
import {
  Autocomplete,
  Dropdown,
  LoadingText,
  DatePicker,
  Button,
  FeatherIcon,
  toast,
  TextInput,
  ErrorMessage,
} from 'frappe-ui'
import { vFocus } from '@/directives'
import { activeUsers } from '@/data/users'
import { useGroupedSpaceOptions } from '@/data/groupedSpaces'
import { useTask } from '@/data/tasks'
import { GPTask } from '@/types/doctypes'
import { useSprintOptions } from '@/composables/useSprintOptions'
import { useDiscussionOptions } from '@/composables/useDiscussionOptions'

const props = defineProps<{ taskId: string }>()

const router = useRouter()
const route = useRoute()
const task = useTask(() => props.taskId)

task.onSuccess((doc) => {
  if (['Task', 'SpaceTask'].includes(route.name as string) && route.params.taskId === doc.name) {
    task.trackVisit.submit()
  }
})

const selectedSpace = computed({
  get() {
    if (!spaceOptions.value) return null

    const projectValue = String(task?.doc?.project || '')

    const allOptions = spaceOptions.value.flatMap(opt =>
      opt.items ? opt.items : [opt]
    )
    return allOptions.find(i => i.value === projectValue) || null
  },
  set(option: { value: string } | null) {
    changeSpace(option)
  }
})





// 🧩 Computed Options
const assignableUsers = computed(() =>
  activeUsers.value.map((user) => ({
    label: user.full_name,
    value: user.name,
  })),
)

const statusOptions = computed(() =>
  (['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled'] as GPTask['status'][]).map(
    (status) => ({
      icon: () => h(TaskStatusIcon, { status }),
      label: status,
      onClick: () => task.setValue.submit({ status }),
    }),
  ),
)

const priorityOptions = computed(() =>
  (['Low', 'Medium', 'High'] as GPTask['priority'][]).map((priority) => ({
    icon: () => h(TaskPriorityIcon, { priority }),
    label: priority,
    onClick: () => task.setValue.submit({ priority }),
  })),
)

const spaceOptions = useGroupedSpaceOptions({ filterFn: (space) => !space.archived_at })
const { formattedSprintOptions, loadSprints } = useSprintOptions()
const { formattedDiscussionOptions, loadDiscussions } = useDiscussionOptions()

watch(
  () => task.doc,
  async (doc) => {
    if (doc?.sub_tasks?.length) {
      doc.sub_tasks.forEach((sub) => {
        // If loaded from DB as collaborators string, rebuild structured array
        if (typeof sub.collaborators === 'string' ) {
          const users = sub.collaborators
            .split(',')
            .map((u) => u.trim())
            .filter(Boolean)

          sub.sub_task_collaborate = users.map((user) => ({
            doctype: 'GP Sub Task Member',
            user,
          }))
        }
      })
    }

    // Load project-related data
    if (doc?.project) {
      await loadSprints(doc.project)
      await loadDiscussions(doc.project)
    }
  },
  { immediate: true },
)

// --- Change Handlers ---
function changeAssignee(option: { value: string } | null) {
  task.setValue.submit({ assigned_to: option?.value || '' })
}

function changeMembers(selected: any[] | null) {
  const memberDocs = (selected || []).map((item) => {
    const user = typeof item === 'string' ? item : item?.value || item?.name
    return { doctype: 'GP Task Member', user }
  })
  task.setValue.submit({ task_collaborate: memberDocs })
}

function changeDiscussion(option: { value: string } | null) {
  task.setValue.submit({ gp_discussion: option?.value || '' })
}

function changeSprint(option: { value: string } | null) {
  task.setValue.submit({ sprint: option?.value || '' })
}

function changeSpace(option: { value: string } | null) {
  if (!task?.doc) return
  task.doc.project = String(option?.value || '')
  task.doc.sprint = ''  
  task.doc.gp_discussion = ''  
  task.setValue.submit({ project: task.doc.project, sprint: '',gp_discussion: '' })
    .then(() => updateRoute())
    .catch(err => console.error('Failed to update project:', err))
}



function updateRoute() {
  if (!task?.doc) return

  router.replace({
    name: task.doc.project ? 'SpaceTask' : 'Task',
    params: task.doc.project
      ? { taskId: task.doc.name, spaceId: task.doc.project }
      : { taskId: task.doc.name },
  })
}



function copyTaskId() {
  if (task.doc.taskid) {
    navigator.clipboard
      .writeText(task.doc.taskid)
      .then(() => toast.success('Copied to clipboard!'))
      .catch(() => toast.error('Failed to copy!'))
  }
}

// --- Sub Task Management ---
function addSubTask() {
  if (!task.doc.sub_tasks) task.doc.sub_tasks = []

  const lastSub = task.doc.sub_tasks.at(-1)
  if (lastSub && !lastSub.title?.trim()) return

  const data = {
    doctype: 'GP Sub Task',
    title: '',
    members: [],
    status: 'Todo',
    due_date: null,
    idx: task.doc.sub_tasks.length + 1,
  }

  task.doc.sub_tasks.push(data)
  saveSubTasks(task.doc.sub_tasks)
}

function removeSubTask(index) {
  if (!task.doc.sub_tasks?.length) return

  task.doc.sub_tasks.splice(index, 1)
  task.doc.sub_tasks.forEach((sub, i) => (sub.idx = i + 1))
  saveSubTasks(task.doc.sub_tasks)
}

// --- Save Logic ---
function saveSubTasks(subTasks) {
  const cleanSubs = normalizeSubTasks(subTasks)

  if (!cleanSubs.length) {
    return
  }

  task.setValue.submit({ sub_tasks: cleanSubs })
}

function statusBadgeClass(status: string) {
  switch (status) {
    case 'Done':
      return 'bg-green-100 text-green-700'
    case 'In Progress':
      return 'bg-blue-100 text-blue-700'
    case 'Todo':
      return 'bg-yellow-100 text-yellow-700'
    case 'Backlog':
      return 'bg-gray-100 text-gray-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function statusDotClass(status: string) {
  switch (status) {
    case 'Done':
      return 'bg-green-500'
    case 'In Progress':
      return 'bg-blue-500'
    case 'Todo':
      return 'bg-yellow-500'
    case 'Backlog':
      return 'bg-gray-400'
    default:
      return 'bg-gray-400'
  }
}


function normalizeSubTasks(subTasks) {
  return (subTasks || []).map((sub) => {
    let sub_task_collaborate = sub.sub_task_collaborate

    // Convert from collaborators string (DB) → structured array
    if (typeof sub.collaborators === 'string' && !Array.isArray(sub_task_collaborate)) {
      const users = sub.collaborators
        .split(',')
        .map((u) => u.trim())
        .filter(Boolean)

      sub_task_collaborate = users.map((user) => ({
        doctype: 'GP Sub Task Member',
        user,
      }))
    }

    // Always keep string version in sync for readability/logging
    const collaboratorsString = Array.isArray(sub_task_collaborate)
      ? sub_task_collaborate.map((c) => c.user).join(', ')
      : sub.collaborators || ''

    return {
      ...sub,
      sub_task_collaborate,
      collaborators: collaboratorsString,
    }
  })
}

// --- Autocomplete Change ---
function handleCollaboratorChange(sub, selected) {
  const collaborators = Array.isArray(selected) ? selected : []

  sub.sub_task_collaborate = collaborators.map((user) => ({
    doctype: 'GP Sub Task Member',
    user: typeof user === 'string' ? user : user?.value || user?.name,
  }))

  sub.collaborators = sub.sub_task_collaborate.map((c) => c.user).join(', ')

  saveSubTasks(task.doc.sub_tasks)
}
</script>

