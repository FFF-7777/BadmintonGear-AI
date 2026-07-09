/**
 * 知识库API
 */
import request from './request'

export function getKnowledgeList(params) {
  return request.get('/knowledge/admin/list', { params })
}

export function uploadKnowledge(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/knowledge/admin/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

export function vectorizeKnowledge(id) {
  return request.post(`/knowledge/admin/${id}/vectorize`, {}, {
    timeout: 600000, // 大文件(3-4MB markdown)向量化需 6-8 分钟，远超默认 30s
  })
}

export function deleteKnowledge(id) {
  return request.delete(`/knowledge/admin/${id}`)
}
