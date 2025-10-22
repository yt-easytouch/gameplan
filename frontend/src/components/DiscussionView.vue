<template>
  <div class="relative flex h-full flex-col" v-if="postId">
    <div class="mx-auto w-full max-w-3xl px-4 xl:px-0">
      <!-- Skeleton Loader -->
      <div v-if="discussion.loading">
        <div
          class="pb-2 pt-14 flex w-full items-center sticky top-0 z-[1] bg-surface-white"
        >
          <Avatar size="lg" label="A" class="mr-3 animate-pulse shrink-0">
            <div></div>
          </Avatar>
          <div class="flex flex-col md:block">
            <div
              class="text-base font-medium bg-surface-gray-2 animate-pulse w-20 h-4"
            ></div>
          </div>
          <div class="ml-auto flex space-x-2">
            <Button>
              <template #icon>
                <div class="animate-pulse w-20 h-8"></div>
              </template>
            </Button>
          </div>
        </div>
        <div class="flex items-start justify-between space-x-1">
          <h1 class="flex items-center text-2xl font-semibold animate-pulse">
            <span class="bg-surface-gray-3 h-5.5 w-32"> </span>
            <span class="bg-surface-gray-3 h-5.5 w-20 ml-2"> </span>
            <span class="bg-surface-gray-3 h-5.5 w-40 ml-2"> </span>
          </h1>
        </div>
      </div>

      <!-- Discussion Content -->
      <template v-else-if="discussion.doc">
        <div>
          <!-- Header -->
          <div
            class="pb-2 pt-14 flex w-full items-center sticky top-0 z-[1] bg-surface-white"
          >
            <UserProfileLink class="mr-3" :user="discussion.doc.owner">
              <UserAvatarWithHover size="lg" :user="discussion.doc.owner" />
            </UserProfileLink>
            <div class="flex flex-col md:block">
              <UserProfileLink
                class="text-base font-medium text-ink-gray-8 hover:text-ink-blue-4"
                :user="discussion.doc.owner"
              >
                {{ $user(discussion.doc.owner).full_name }}
                <span class="hidden md:inline text-ink-gray-7"
                  >&nbsp;&middot;&nbsp;</span
                >
              </UserProfileLink>
              <Tooltip
                :text="dayjsLocal(discussion.doc.creation).format('D MMM YYYY [at] h:mm A')"
              >
                <time
                  class="text-base text-ink-gray-5"
                  :datetime="discussion.doc.creation"
                >
                  {{ dayjsLocal(discussion.doc.creation).fromNow() }}
                </time>
              </Tooltip>
            </div>
            <div class="ml-auto flex space-x-2">
              <Dropdown
                v-if="!readOnlyMode"
                class="ml-auto"
                placement="right"
                :button="{
                  icon: 'more-horizontal',
                  variant: 'ghost',
                  label: 'Discussion Options',
                }"
                :options="actions"
              />
            </div>
          </div>

          <!-- Title + Issue Type -->
          <div :class="{ 'pb-4 mt-1': !editingPost }">
            <div class="flex items-start justify-between space-x-1">
              <h1
                v-if="!editingPost"
                class="flex items-center text-2xl font-semibold"
              >
                <Tooltip
                  v-if="discussion.doc.closed_at"
                  text="This discussion is closed"
                >
                  <LucideLock
                    class="mr-2 h-4 w-4 text-ink-gray-6"
                    :stroke-width="2"
                  />
                </Tooltip>
                <span class="text-ink-gray-8">
                  {{ discussion.doc.title }}
                </span>
              </h1>
              <!-- 🧩 Issue Type Combobox -->
                <div class="m-4 w-full max-w-sm">
                    <template v-if="editingPost">
                      <Combobox
                        :options="formattedIssueTypeOptions"
                        v-model="discussion.doc.issue_type"
                        placeholder="Select Issue Type"
                        class="w-full"
                      />
                    </template>

                    <template v-else>
                      <label class="block text-gray-800 font-medium">
                        {{ discussion.doc.issue_type || 'No issue type selected' }}
                      </label>
                    </template>
                  </div>

              
            </div>
            
            
            <!-- Participants -->
            <div class="mt-2 flex items-center text-base" v-show="!editingPost">
              <span class="text-ink-gray-5">
                {{
                  discussion.doc.participants_count == 1
                  ? `1 participant`
                  : `${discussion.doc.participants_count} participants`
                }}
              </span>
            
              
              <template v-if="discussion.doc.views > 1">
                <span class="px-1.5 text-ink-gray-7">&middot;</span>
                <span class="text-ink-gray-5">
                  {{ discussion.doc.views }} views
                </span>
              </template>
            </div>
          </div>

          <!-- Content -->
          <div
            :class="{
              'rounded-lg border p-4 focus-within:border-outline-gray-3':
                editingPost,
            }"
            ref="mainPostContentEl"
          >
            <div v-if="editingPost" class="w-full">
              <div class="mb-2">
                <input
                  v-if="editingPost"
                  type="text"
                  class="w-full rounded border-0 text-ink-gray-8 px-0 py-0.5 text-2xl font-semibold focus:ring-0"
                  ref="title"
                  v-model="discussion.doc.title"
                  placeholder="Title"
                  v-focus
                />
              </div>
            </div>
            <CommentEditor
              :value="discussion.doc.content"
              @change="discussion.doc.content = $event"
              :submitButtonProps="{
                variant: 'solid',
                onClick: updatePost,
                loading: discussion.setValue.loading,
              }"
              :discardButtonProps="{
                onClick: () => {
                  editingPost = false
                  discussion.reload()
                },
              }"
              :editable="editingPost"
            />
          </div>

          <!-- Reactions -->
          <div class="mt-3">
            <Reactions
              doctype="GP Discussion"
              :name="discussion.doc.name"
              v-model:reactions="discussion.doc.reactions"
              :read-only-mode="readOnlyMode"
            />
          </div>
        </div>

        <!-- Comments -->
        <CommentsArea
          doctype="GP Discussion"
          :name="discussion.doc.name"
          :newCommentsFrom="discussion.doc.last_unread_comment?.toString()"
          :read-only-mode="readOnlyMode"
          :disable-new-comment="Boolean(discussion.doc.closed_at)"
          @rich-quote="handleRichQuote"
          @rich-quote-click="handleRichQuoteClick"
          ref="commentsArea"
        />

        <!-- Move Dialog -->
        <Dialog
          :options="{ title: 'Move discussion to another space' }"
          @close="
            () => {
              discussionMoveDialog.project = null
            }
          "
          v-model="discussionMoveDialog.show"
        >
          <template #body-content>
            <Autocomplete
              :options="spaceOptions"
              v-model="discussionMoveDialog.project"
              placeholder="Select a project"
            />
            <ErrorMessage class="mt-2" :message="discussion.moveToProject.error" />
          </template>
          <template #actions>
            <Button
              class="w-full"
              variant="solid"
              :loading="discussion.moveToProject.loading"
              @click="moveToSpace"
            >
              {{
                discussionMoveDialog.project
                  ? `Move to ${discussionMoveDialog.project.label}`
                  : 'Move'
              }}
            </Button>
          </template>
        </Dialog>

        <RevisionsDialog
          v-model="showRevisionsDialog"
          doctype="GP Discussion"
          :name="discussion.doc.name"
          fieldname="content"
        />
      </template>
    </div>

    <!-- Scroll to top -->
    <div v-if="!isMobile" class="fixed bottom-3 h-9 grid place-content-center right-3 z-[2]">
      <Button variant="ghost" v-show="isScrolled" @click="scrollToTop">
        <template #prefix>
          <LucideArrowUp class="h-5 w-5 text-ink-gray-6" />
        </template>
        Scroll to top
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, reactive, useTemplateRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Autocomplete, Avatar, Dropdown, Dialog, Tooltip, usePageMeta, dayjsLocal } from 'frappe-ui'
import { until } from '@vueuse/core'
import Reactions from './Reactions.vue'
import UserAvatarWithHover from './UserAvatarWithHover.vue'
import CommentsArea from '@/components/CommentsArea.vue'
import CommentEditor from './CommentEditor.vue'
import UserProfileLink from './UserProfileLink.vue'
import RevisionsDialog from './RevisionsDialog.vue'
import { vFocus } from '@/directives'
import { copyToClipboard } from '@/utils'
import { useSpace } from '@/data/spaces'
import { useGroupedSpaceOptions } from '@/data/groupedSpaces'
import { useDiscussion } from '@/data/discussions'
import { tags } from '@/data/tags'
import { createDialog } from '@/utils/dialogs'
import { useScrollPosition } from '@/utils/scrollContainer'
import { isMobile } from '@/utils/composables'
import { useRichQuoteHandler } from '@/components/RichQuoteExtension/useRichQuoteHandler'

import LucideArrowUp from '~icons/lucide/arrow-up'
import LucideLock from '~icons/lucide/lock'
import Combobox from 'frappe-ui/src/components/Combobox/Combobox.vue'
import { useIssueTypeOptions } from '@/composables/useIssueTypeOptions'

// ✅ Import issue type composable
const { formattedIssueTypeOptions, loading } = useIssueTypeOptions()

const props = defineProps<{
  postId: string
  readOnlyMode?: boolean
}>()

const router = useRouter()
const route = useRoute()
const commentsArea = useTemplateRef('commentsArea')
const mainPostContentEl = ref<HTMLElement | null>(null)
const { isScrolled, scrollToTop } = useScrollPosition()
const { handleRichQuote, handleRichQuoteClick } = useRichQuoteHandler(commentsArea, mainPostContentEl)

const editingPost = ref(false)
const discussionMoveDialog = reactive({
  show: false,
  project: null as { label: string; value: string } | null,
})
const showRevisionsDialog = ref(false)

const discussion = useDiscussion(() => props.postId)

onMounted(() => {
  scrollToUnread()
})

async function scrollToUnread() {
  if (!discussion.doc) await until(() => discussion.doc).toBeTruthy()
  updateUrlSlug()

  const doc = discussion.doc
  if (!route.query.comment && (doc?.last_unread_comment || doc?.last_unread_poll)) {
    router.replace({
      query: {
        comment: doc.last_unread_comment || undefined,
        poll: doc.last_unread_poll || undefined,
      },
    })
  }

  if (route.name === 'Discussion' && route.params.postId === doc.name) {
    discussion.trackVisit.submit()
  }
}

function copyLink() {
  copyToClipboard(`${window.location.origin}${window.location.pathname}`)
}

function moveToSpace() {
  if (!discussionMoveDialog.project?.value) return
  discussion.moveToProject
    .submit({ project: discussionMoveDialog.project.value })
    .then(() => {
      nextTick(() => {
        discussionMoveDialog.show = false
        discussionMoveDialog.project = null
        router.replace({
          name: 'Discussion',
          params: { spaceId: discussion.doc?.project, postId: discussion.doc?.name },
        })
      })
    })
    .catch(() => (discussionMoveDialog.show = true))
}

function updatePost() {
  discussion.setValue
    .submit({
      title: discussion.doc?.title,
      content: discussion.doc?.content,
      issue_type: discussion.doc?.issue_type,
    })
    .then(() => tags.reload())
  editingPost.value = false
}

function updateUrlSlug() {
  const doc = discussion.doc
  if (!doc) return
  if (!route.params.slug || route.params.slug !== doc.slug) {
    nextTick(() => {
      router.replace({
        name: 'Discussion',
        params: { ...route.params, slug: doc.slug },
        query: route.query,
      })
    })
  }
}

const space = useSpace(() => discussion.doc?.project)
const spaceOptions = useGroupedSpaceOptions({
  filterFn: (space) => !space.archived_at && space.name !== discussion.doc?.project,
})

// Dropdown actions
const actions = computed(() => [
  { label: 'Edit', icon: 'edit', onClick: () => (editingPost.value = true) },
  { label: 'Revisions', icon: 'rotate-ccw', onClick: () => (showRevisionsDialog.value = true) },
  { label: 'Copy link', icon: 'link', onClick: copyLink },
])

usePageMeta(() => {
  if (!discussion.doc) return
  const space = useSpace(() => discussion.doc?.project)
  if (!space) return
  return {
    title: [discussion.doc.title, space.value?.title].filter(Boolean).join(' - '),
  }
})
</script>
