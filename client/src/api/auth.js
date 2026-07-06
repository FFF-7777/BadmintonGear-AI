/**
 * 认证相关API
 */
import request from './request'

/** 管理员登录 */
export function adminLogin(data) {
  return request.post('/auth/admin/login', data)
}
