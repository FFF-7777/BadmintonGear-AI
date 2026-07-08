import axios from 'axios'
import { buildSpecList } from '@/utils/specs'

const http = axios.create({ baseURL: '/api', timeout: 15000 })

const TOKEN_KEY = 'bg_chat_token'
const USER_KEY = 'bg_chat_user'

function getStored(key) {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}
function setStored(key, val) {
  try {
    localStorage.setItem(key, val)
  } catch {
    /* ignore */
  }
}

// 自动匿名登录：首次访问时注册一个 guest 用户并登录，token 存 localStorage
// 这样聊天前端无需独立的登录页即可使用后端真实 AI 能力
export async function ensureToken() {
  const existing = getStored(TOKEN_KEY)
  if (existing) return existing

  let username = getStored(USER_KEY)
  if (!username) {
    username = 'guest_' + Math.random().toString(36).slice(2, 10)
    setStored(USER_KEY, username)
  }
  const password = 'guest123'

  try {
    await http.post('/auth/user/register', {
      username,
      password,
      type: 'user',
      nickname: '访客',
    })
  } catch (e) {
    // 用户名已存在属于正常情况，忽略
    const code = e?.response?.data?.code
    if (code !== 400) {
      // 其他错误也尝试继续登录
    }
  }

  const loginRes = await http.post('/auth/user/login', { username, password })
  const token = loginRes?.data?.data?.token
  if (!token) throw new Error('登录失败：未返回 token')
  setStored(TOKEN_KEY, token)
  return token
}

function mapProduct(p) {
  if (!p) return null
  const specs = p.specs && typeof p.specs === 'object' ? p.specs : {}
  const specList = buildSpecList(specs)
  return {
    id: p.id,
    brand: p.brand || specs.brand || specs.Brand || specs.品牌 || '',
    series: p.series || '',
    brandId: '',
    category: p.category_id || '',
    categoryName: p.category_name || '',
    title: p.name || '装备',
    summary: p.reason || p.category_name || '管理员维护的装备条目',
    priceRange: typeof p.price === 'number' ? `¥${p.price}` : String(p.price || ''),
    level: specs.level || specs.stage || '装备对比',
    bestFor: p.reason || p.category_name || '',
    specs: specList.length ? specList : [p.category_name || '装备'],
    tags: [...(Array.isArray(p.tags) ? p.tags : []), ...(Array.isArray(p.manual_tags) ? p.manual_tags : [])].filter(Boolean),
    image: p.image || specs.image || '',
    score: p.score,
    raw: p,
  }
}

/**
 * 通过 WebSocket 连接后端流式 AI 聊天
 * @param {string} message 用户消息
 * @param {string} sessionId 会话ID（可空）
 * @param {object} handlers { onSession, onContent, onDone, onError }
 *   - onContent(delta): 流式文本增量
 *   - onDone(payload): 完整结果 { answer, sources, recommended_products }
 */
export function chatStream(message, sessionId, handlers = {}) {
  const token = getStored(TOKEN_KEY)
  if (!token) {
    handlers.onError?.(new Error('缺少认证 token'))
    return null
  }

  // token 不再走 query 参数（会进访问日志），改由首条消息传递
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${proto}//${location.host}/api/chat/ws`

  let ws
  try {
    ws = new WebSocket(wsUrl)
  } catch (e) {
    handlers.onError?.(e)
    return null
  }

  let settled = false
  let authenticated = false

  const done = (fn) => {
    if (settled) return
    settled = true
    fn()
  }

  ws.onopen = () => {
    // 首条消息发送认证
    ws.send(JSON.stringify({ type: 'auth', token }))
  }

  ws.onmessage = (ev) => {
    let data
    try {
      data = JSON.parse(ev.data)
    } catch {
      return
    }

    // 认证阶段
    if (!authenticated) {
      if (data.type === 'auth_ok') {
        authenticated = true
        ws.send(JSON.stringify({ message, session_id: sessionId || '' }))
      } else if (data.type === 'error') {
        done(() => handlers.onError?.(new Error(data.message || '认证失败')))
      }
      return
    }

    // 业务消息
    switch (data.type) {
      case 'session_id':
        handlers.onSession?.(data.session_id)
        break
      case 'content':
        handlers.onContent?.(data.content || '')
        break
      case 'sources':
        handlers.onSources?.(data.sources || [])
        break
      case 'done':
        done(() => {
          const products = (data.recommended_products || []).map(mapProduct).filter(Boolean)
          handlers.onDone?.({
            answer: data.answer || '',
            sources: data.sources || [],
            recommended_products: products,
          })
        })
        break
      case 'error':
        done(() => handlers.onError?.(new Error(data.message || '服务异常')))
        break
      default:
        break
    }
  }

  ws.onerror = () => {
    done(() => handlers.onError?.(new Error('WebSocket 连接失败')))
  }

  ws.onclose = () => {
    done(() => {})
  }

  return ws
}

export { mapProduct }
