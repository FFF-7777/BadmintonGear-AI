/**
 * 用户管理API
 */
import request from './request'

export function getUserList(params) {
  return request.get('/admin/user/list', { params })
}

export function updateUserStatus(id, status) {
  return request.put(`/admin/user/${id}/status`, { status })
}
