/**
 * 管理员个人资料 API
 */
import request from './request'

/** 获取当前管理员资料 */
export function getAdminProfile() {
  return request.get('/admin/profile/me')
}

/** 更新管理员资料 */
export function updateAdminProfile(data) {
  return request.put('/admin/profile', data)
}

/** 修改管理员密码 */
export function changeAdminPassword(data) {
  return request.put('/admin/profile/password', data)
}

/** 上传头像图片 */
export function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload/image?type=avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
