import { request } from './http'
import type { UserItem, UserRole } from '@/types/api'

export function listUsersApi() {
  return request<UserItem[]>({
    url: '/users',
    method: 'get',
  })
}

export function createUserApi(body: { username: string; password: string; role: UserRole }) {
  return request<UserItem>({
    url: '/users',
    method: 'post',
    data: body,
  })
}

export function patchUserApi(
  id: number,
  body: { role?: UserRole; isActive?: boolean; password?: string },
) {
  return request<UserItem>({
    url: `/users/${id}`,
    method: 'patch',
    data: body,
  })
}
