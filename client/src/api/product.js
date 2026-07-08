/**
 * 装备API
 */
import request from './request'

export function getProductList(params) {
  return request.get('/product/admin/list', { params })
}

export function createProduct(data) {
  return request.post('/product/admin/create', data)
}

export function updateProduct(id, data) {
  return request.put(`/product/admin/${id}`, data)
}

export function deleteProduct(id) {
  return request.delete(`/product/admin/${id}`)
}

export function uploadImage(file, type = 'product') {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/upload/image?type=${type}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function importProducts(file, categoryId) {
  const formData = new FormData()
  formData.append('file', file)
  const suffix = categoryId ? `?category_id=${categoryId}` : ''
  return request.post(`/product/admin/import${suffix}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function downloadImportTemplate(categoryId) {
  return request.get('/product/admin/import-template', {
    params: { category_id: categoryId },
    responseType: 'blob',
  })
}
