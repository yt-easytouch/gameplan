import { computed, MaybeRefOrGetter, toValue } from 'vue'
import { useCall } from 'frappe-ui/src/data-fetching'
import { GPProject, GPMember } from '@/types/doctypes'

interface Member extends Pick<GPMember, 'user'> {}

export interface Space
  extends Pick<
    GPProject,
    | 'name'
    | 'title'
    | 'icon'
    | 'team'
    | 'archived_at'
    | 'is_private'
    | 'modified'
    | 'tasks_count'
    | 'discussions_count'
  > {
  members: Member[]
}

export const spaces = useCall<Space[]>({
  url: '/api/method/gameplan.api.get_gp_projects_with_members',
  cacheKey: 'spaces',
  initialData: [],
  transform(data) {
    for (let space of data) {
      space.name = space.name.toString()
    }
    return data
  },
  immediate: true,
  onSuccess() {
    unreadCount.submit()
  },
})

export function useSpace(name: MaybeRefOrGetter<string | undefined>) {
  return computed(() => {
    const _name = toValue(name)
    if (!_name) return null
    return spaces.data?.find((space) => space.name.toString() === _name.toString()) ?? null
  })
}

export const joinedSpaces = useCall<string[]>({
  url: '/api/v2/method/GP Project/get_joined_spaces',
  cacheKey: 'joinedSpaces',
  initialData: [],
})

export function hasJoined(spaceId: MaybeRefOrGetter<string>) {
  return joinedSpaces.data?.includes(toValue(spaceId))
}

export const unreadCount = useCall<{ [spaceId: number]: number }>({
  url: '/api/v2/method/GP Project/get_unread_count',
  immediate: false,
  cacheKey: 'unreadCount',
})

export function getSpaceUnreadCount(spaceId: string) {
  const spaceIdInt = parseInt(spaceId)
  return unreadCount.data?.[spaceIdInt] ?? 0
}
