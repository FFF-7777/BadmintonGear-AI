import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

function clearAdminSession() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_username')
  localStorage.removeItem('admin_nickname')
  localStorage.removeItem('admin_avatar')
}

function redirectToLogin() {
  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
  } else {
    router.replace('/login')
  }
}

function statusMessage(status) {
  const map = {
    400: '请求参数有误，请检查填写内容',
    401: '登录已失效，请重新登录',
    403: '当前账号没有权限执行该操作',
    404: '接口不存在或数据已被删除',
    500: '后端服务异常，请检查数据库和服务日志',
    502: '后端服务未启动或代理连接失败',
  }
  return map[status] || `请求失败，状态码${status}`
}

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    if (response.config?.responseType === 'blob') {
      return response
    }
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.msg || statusMessage(res.code))
      if (res.code === 401) {
        clearAdminSession()
        redirectToLogin()
      }
      return Promise.reject(new Error(res.msg || statusMessage(res.code)))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    ElMessage.error(status ? statusMessage(status) : '网络连接失败，请确认服务是否启动')
    if (status === 401) {
      clearAdminSession()
      redirectToLogin()
    }
    return Promise.reject(error)
  }
)

export default request
