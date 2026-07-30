import { request } from './http'
import type { LoginResult } from '@/types/api'

export function loginApi(username: string, password: string) {
  return request<LoginResult>({
    url: '/auth/login',
    method: 'post',
    data: { username, password },
  })
}

export function meApi() {
  return request<{ username: string }>({
    url: '/auth/me',
    method: 'get',
  })
}

export function changePasswordApi(oldPassword: string, newPassword: string) {
  return request<null>({
    url: '/auth/change-password',
    method: 'post',
    data: { oldPassword, newPassword },
  })
}
