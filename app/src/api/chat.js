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

// 清除无效 token（供 chatStream 认证失败时调用）
function clearInvalidToken() {
  setStored(TOKEN_KEY, '')
}

// ── 对话历史持久化（按 token 分键）──
// 目的：SPA 内页面跳转（如去「装备库」再返回）或刷新页面时保留对话；
// 仅在 token 换新（≈ 下一次登录）时自然开启一份空历史，符合"下次登录才消失"。
const HISTORY_PREFIX = 'bg_chat_history_'

export function getChatHistory() {
  const token = getStored(TOKEN_KEY)
  if (!token) return null
  try {
    const raw = localStorage.getItem(HISTORY_PREFIX + token)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveChatHistory(state) {
  const token = getStored(TOKEN_KEY)
  if (!token) return
  try {
    localStorage.setItem(HISTORY_PREFIX + token, JSON.stringify(state))
  } catch {
    /* 容量超限等忽略 */
  }
}

export function clearChatHistory() {
  const token = getStored(TOKEN_KEY)
  if (!token) return
  try {
    localStorage.removeItem(HISTORY_PREFIX + token)
  } catch {
    /* ignore */
  }
}

// 生成符合后端约束的随机用户名（≤20字符）
function makeGuestName() {
  return 'g' + Math.random().toString(36).slice(2, 17) // 1+15=16，远低于 20 上限
}

// 自动匿名登录：确保拿到一个有效的 JWT token
// 策略：验证缓存 token → 先尝试登录（用户可能已存在）→ 登录失败才注册 → 多用户名兜底
export async function ensureToken() {
  const password = 'guest123'

  // ── Step 1: 验证已有缓存 token ──
  const existing = getStored(TOKEN_KEY)
  if (existing) {
    try {
      await http.get('/user/profile/me', { headers: { Authorization: `Bearer ${existing}` } })
      return existing
    } catch (e) {
      clearInvalidToken()
    }
  }

  // ── Step 2: 拿到候选用户名（优先用 localStorage 里之前成功注册过的）──
  let username = getStored(USER_KEY)
  if (!username || username.length > 20 || !/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
    username = makeGuestName()
    setStored(USER_KEY, username)
  }

  // ── Step 3: 先尝试直接登录（用户可能已在之前的会话中注册过）──
  try {
    const loginRes = await http.post('/auth/user/login', { username, password })
    const token = loginRes?.data?.data?.token
    if (token) {
      setStored(TOKEN_KEY, token)
      return token
    }
  } catch {
    // 登录失败后进入注册流程。
  }

  // ── Step 4: 登录失败 → 注册新用户 ──
  try {
    await http.post('/auth/user/register', {
      username, password, type: 'user', nickname: '访客',
    })
  } catch (e) {
    const status = e?.response?.status

    // 422=参数问题(用户名格式/太长等) → 换名重试
    if (status === 422) {
      username = makeGuestName()
      setStored(USER_KEY, username)
      try {
        await http.post('/auth/user/register', { username, password, type: 'user', nickname: '访客' })
      } catch {
        // 由后续登录统一返回最终认证错误。
      }
    }
    // 400=用户名已存在（但登录却失败了？可能是密码不一致，忽略）
    // 429=限流 → 稍后重试或换策略
  }

  // ── Step 5: 注册后（或注册被跳过）再次登录 ──
  try {
    const loginRes = await http.post('/auth/user/login', { username, password })
    const token = loginRes?.data?.data?.token
    if (token) {
      setStored(TOKEN_KEY, token)
      return token
    }
    throw new Error('登录无返回 token: ' + JSON.stringify(loginRes?.data))
  } catch (e) {
    const detail = e?.response?.data || e.message || String(e)
    console.error('[ensureToken] ❌ 登录最终失败:', detail)

    // ── Step 6: 终极兜底 —— 尝试用全新用户名注册+登录（最多 3 次）──
    for (let attempt = 0; attempt < 3; attempt++) {
      const freshName = makeGuestName()
      try {
        await http.post('/auth/user/register', { username: freshName, password, type: 'user', nickname: '访客' })
        const lr = await http.post('/auth/user/login', { username: freshName, password })
        const t = lr?.data?.data?.token
        if (t) {
          setStored(USER_KEY, freshName)
          setStored(TOKEN_KEY, t)
          return t
        }
      } catch {
        // 尝试下一个随机访客账号。
      }
    }
    throw new Error('认证失败: ' + (typeof detail === 'string' ? detail.slice(0, 200) : JSON.stringify(detail)))
  }
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
    confidence: p.confidence || '',
    sourceConfidence: p.source_confidence || '',
    recommendationRole: p.recommendation_role || '',
    risk: Array.isArray(p.risk) ? p.risk : [],
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
        // 认证失败 → 清除无效 token，下次消息会重新登录
        clearInvalidToken()
        done(() => handlers.onError?.(new Error(data.message || '认证失败')))
      }
      return
    }

    // 业务消息
    switch (data.type) {
      case 'session_id':
        handlers.onSession?.(data.session_id)
        break
      case 'content': {
        const c = data.content || ''
        handlers.onContent?.(c)
        break
      }
      case 'sources':
        handlers.onSources?.(data.sources || [])
        break
      case 'done':
        done(() => {
          const raw = data.recommended_products || []
          const products = raw.map(mapProduct).filter(Boolean)
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
