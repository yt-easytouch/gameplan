<template>
  <div>
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-5 py-2.5"
    >
      <SpaceBreadcrumbs
        v-if="space"
        :spaceId="space.name"
        :items="[
          {
            label: 'Sprints',
            route: { name: 'SpaceSprints' },
          },
          {
            label: sprint.doc ? sprint.doc.title : route.params.sprintId.toString(),
            route: { name: 'Sprint' },
          },
        ]"
      />
      <Breadcrumbs
        v-else
        class="h-7"
        :items="[
          {
            label: 'My Sprints',
            route: { name: 'MySprints' },
          },
          {
            label: sprint.doc ? sprint.doc.title : route.params.sprintId.toString(),
            route: { name: 'Sprint' },
          },
        ]"
      />
    </header>
    <div>
      <SprintDetail :sprintId="sprintId" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Breadcrumbs, usePageMeta } from 'frappe-ui'
import SpaceBreadcrumbs from '@/components/SpaceBreadcrumbs.vue'
import { useSprint } from '@/data/sprints'
import { useSpace } from '@/data/spaces'
import SprintDetail from '@/components/SprintDetail.vue'

const props = defineProps<{ sprintId: string }>()
const sprint = useSprint(() => props.sprintId)
const space = useSpace(() => sprint.doc?.project)
const route = useRoute()

usePageMeta(() => {
  return {
    title: `${sprint.doc?.title} | ${space.value?.title || 'My Sprints'}`,
  }
})
</script>
