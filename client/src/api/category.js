/**
 * 装备分类API
 */
import request from './request'

export function getCategoryList(params) {
  return request.get('/category/admin/list', { params })
}

export function getAllCategories() {
  return request.get('/category/list')
}

export function createCategory(data) {
  return request.post('/category/admin/create', data)
}

export function updateCategory(id, data) {
  return request.put(`/category/admin/${id}`, data)
}

export function deleteCategory(id) {
  return request.delete(`/category/admin/${id}`)
}
