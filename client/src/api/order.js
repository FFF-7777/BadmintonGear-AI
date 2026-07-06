/**
 * 订单API
 */
import request from './request'

export function getOrderList(params) {
  return request.get('/order/admin/list', { params })
}

export function updateOrderStatus(id, status) {
  return request.put(`/order/admin/${id}/status`, { status })
}
