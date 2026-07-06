/**
 * Dashboard统计API
 */
import request from './request'

/** 获取Dashboard统计数据 */
export function getDashboardStats() {
  return request.get('/dashboard/stats')
}
