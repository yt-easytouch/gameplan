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
            :modelValue="task.doc.project"
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
        <div>Task Members</div>
        <div>
          <Autocomplete
            :options="assignableUsers"
            :modelValue="task.doc.members?.map((m) => m.user) || []"
            @update:modelValue="changeMembers"
            placeholder="Members"
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

// --- Computed Options ---
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
  () => task.doc.project,
  async (project) => {
    if (project) {
      await loadSprints(project)
      await loadDiscussions(project)
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
  task.setValue.submit({ members: memberDocs })
}


function changeDiscussion(option: { value: string } | null) {
  task.setValue.submit({ gp_discussion: option?.value || '' })
}

function changeSprint(option: { value: string } | null) {
  task.setValue.submit({ sprint: option?.value || '' })
}

function changeSpace(option: { value: string } | null) {
  if (!task.doc) return
  task.doc.project = option?.value || undefined
  task.setValue.submit({ project: option?.value || '' }).then(updateRoute)
}

// --- Helpers ---
function updateRoute() {
  if (task.doc) {
    router.replace({
      name: task.doc.project ? 'SpaceTask' : 'Task',
      params: task.doc.project
        ? { taskId: task.doc.name, spaceId: task.doc.project }
        : { taskId: task.doc.name },
    })
  }
}

function copyTaskId() {
  if (task.doc.taskid) {
    navigator.clipboard
      .writeText(task.doc.taskid)
      .then(() => toast.success('Copied to clipboard!'))
      .catch(() => toast.error('Failed to copy!'))
  }
}
</script>
