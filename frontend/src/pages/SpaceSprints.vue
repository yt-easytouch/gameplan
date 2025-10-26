<template>
  <div>
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 sm:px-5 py-2.5"
    >
      <Breadcrumbs class="h-7" :items="[{ label: 'My Sprint', route: { name: 'MySprints' } }]" />
      <Button variant="solid" @click="openNewSprintDialog">
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
        Add new
      </Button>
    </header>

    <div class="mx-auto w-full max-w-4xl px-3 sm:px-5">
      <div class="flex pt-3 sm:pt-5">
        <TabButtons
          :buttons="[
            { label: 'All', value: 'all' },
            { label: 'Created by me', value: 'owner' },
          ]"
          v-model="currentTab"
        />
      </div>
      <div class="pb-6 mt-3 sm:mt-4">
        <SprintList
          :listOptions="{ filters, pageLength: 999999 }"
          :groupByStatus="true"
          ref="sprintList"
        />
      </div>
    </div>

    <!-- Include NewSprintDialog here -->
    <NewSprintDialog />
  </div>
</template>

<script setup lang="ts">
import { ref, useTemplateRef } from 'vue'
import { usePageMeta, Breadcrumbs, TabButtons } from 'frappe-ui'
import {  useUser } from '@/data/users'
import SprintList from '@/components/SprintList.vue'
import { showNewSprintDialog,NewSprintDialog } from '@/components/NewSprintDialog'
let sprintList = useTemplateRef<typeof SprintList>('sprintList')
let currentTab = ref('all')

let filters = () => {
  let me =  useUser().name
  return {
    all: { assigned_or_owner: me },
    owner: { owner: me },
  }[currentTab.value]
}

function openNewSprintDialog() {
  console.log("Haaaa")
  showNewSprintDialog({
    onSuccess: () => {
      sprintList.value?.sprint.reload()
    },
  })
}

usePageMeta(() => {
  return {
    title: 'My Sprint',
  }
})
</script>
