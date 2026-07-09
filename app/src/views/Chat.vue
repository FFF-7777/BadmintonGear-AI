<template>
  <div class="chat-page">
    <div class="chat-shell">
      <section class="chat-header">
        <div class="chat-header-copy">
          <span class="chat-eyebrow">羽智选 · RAG AI 装备顾问</span>
          <h1>把预算、打法和具体型号直接说出来</h1>
        </div>

        <div class="chat-header-side">
          <div class="header-cap-grid">
            <span v-for="item in headerCaps" :key="item" class="header-cap">{{ item }}</span>
          </div>

          <button class="header-newchat" :disabled="loading" @click="resetChat">新对话</button>

          <div v-if="ctxBrand" class="header-brand" :style="{ '--bc': ctxBrand.color }">
            <span>优先参考 <b>{{ ctxBrand.nameCn }}</b></span>
            <button class="header-brand-clear" @click="clearCtx">清除</button>
          </div>
        </div>
      </section>

      <div class="chat-scroll" ref="scrollEl" @scroll="handleScroll">
        <div class="chat-column">
          <div v-if="errorText" class="status-card status-card--error">
            <div>
              <strong>后端回答暂时失败</strong>
              <p>{{ errorText }}</p>
            </div>
            <button @click="retryLast">重试上一条</button>
          </div>

          <Transition name="fade">
            <section v-if="showSuggestions" class="welcome-panel">
              <div class="welcome-copy">
                <AiMark :size="46" soft />
                <div>
                  <h2>先给我预算、打法、水平</h2>
                  <p>问具体型号我会先按型号查；资料不全就直接说缺什么，不会乱编参数。</p>
                </div>
              </div>

              <div class="suggest-grid">
                <button v-for="q in suggestions" :key="q" class="suggest-chip" @click="askNow(q)">
                  {{ q }}
                </button>
              </div>
            </section>
          </Transition>

          <div
            v-for="m in messages"
            :key="m.id"
            class="message"
            :class="m.role === 'user' ? 'message--user' : 'message--assistant'"
          >
            <div v-if="m.role === 'assistant'" class="assistant-meta">
              <AiMark :size="34" soft />
              <div class="assistant-meta-copy">
                <strong>羽智选 AI</strong>
                <span v-if="m.streaming">正在生成</span>
                <span v-else-if="m.sources?.length">参考 {{ m.sources.length }} 份资料</span>
                <span v-else>真实后端回答</span>
              </div>
            </div>

            <div class="message-bubble" :class="m.role === 'user' ? 'message-bubble--user' : 'message-bubble--assistant'">
              <div v-if="m.role === 'user'" class="message-plain">{{ m.content }}</div>
              <!-- 流式中的消息用独立 streamingText ref 直接绑定，保证逐字渲染可靠 -->
              <MarkdownView v-else-if="m.streaming && m.id === streamState.aiId" :content="streamingText" />
              <MarkdownView v-else :content="m.content" />
            </div>

            <div v-if="m.role === 'assistant' && m.products?.length" class="reco-panel">
              <div class="reco-panel-head">
                <span>推荐装备</span>
                <b>基于当前问题命中的结构化装备库</b>
              </div>
              <div class="reco-grid">
                <ProductRecoCard v-for="product in m.products" :key="product.id" :product="product" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="composer-shell">
        <div class="composer-card">
          <div class="composer-status">
            <span>{{ loading ? '正在生成真实后端回答' : '已连接真实后端问答链路' }}</span>
            <small>热身、训练、步法等羽毛球周边问题也能问</small>
          </div>

          <div class="composer-main">
            <textarea
              v-model.trim="inputText"
              class="composer-input"
              rows="1"
              placeholder="例如：预算 800，双打后场，想找一支杀球更扎实但别太难上手的球拍"
              @keydown.enter.exact.prevent="askNow()"
            />
            <button class="composer-send" :disabled="loading || !inputText" @click="askNow()">
              {{ loading ? '生成中' : '发送' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getBrand } from '@/data/knowledge'
import { ensureToken, chatStream, getChatHistory, saveChatHistory, clearChatHistory } from '@/api/chat'
import AiMark from '@/components/AiMark.vue'
import MarkdownView from '@/components/MarkdownView.vue'
import ProductRecoCard from '@/components/ProductRecoCard.vue'

defineOptions({ name: 'Chat' })

const route = useRoute()

const scrollEl = ref(null)
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const errorText = ref('')
const sessionId = ref('')
const ctxBrandId = ref('')
const lastQuestion = ref('')
const atBottom = ref(true)
const wsRef = ref(null)
const streamState = reactive({
  aiId: null,
})

// 独立 ref 存放当前流式增量文本，模板直接绑定，绕开「数组内对象→computed→v-html」响应式链
const streamingText = ref('')

// 仅对滚动做 rAF 节流，避免流式期间频繁 scrollTop 触发抖动
let rafScrollId = null

const suggestions = [
  'YY 天斧 77 Pro 和 JS-12 有什么区别？',
  '预算 600 元，新手第一支球拍怎么选？',
  '宽脚球鞋应该优先看哪些参数？',
  '打羽毛球前怎么热身更稳妥？',
]

const headerCaps = ['型号级查找', '双拍固定维度对比', '热身训练也能问']
const ctxBrand = computed(() => (ctxBrandId.value ? getBrand(ctxBrandId.value) : null))
const showSuggestions = computed(() => messages.value.length === 0 && !loading.value)

function resetChat() {
  closeSocket()
  if (streamRafId) { cancelAnimationFrame(streamRafId); streamRafId = null }
  deltaBuffer = ''
  streamState.aiId = null
  streamingText.value = ''
  messages.value = []
  sessionId.value = ''
  ctxBrandId.value = ''
  // 手动清空时也清掉持久化历史
  clearChatHistory()
}

// 从 localStorage 恢复当前登录(token)下的对话；token 不变则跨跳转/刷新都在。
function restoreChat() {
  const data = getChatHistory()
  streamState.aiId = null
  streamingText.value = ''
  if (data && Array.isArray(data.messages)) {
    // 恢复时把残留的 streaming 标记复位，避免卡片卡在"正在生成"
    messages.value = data.messages.map((m) => ({ ...m, streaming: false }))
    sessionId.value = data.sessionId || ''
    ctxBrandId.value = data.ctxBrandId || ''
  } else {
    messages.value = []
    sessionId.value = ''
    ctxBrandId.value = ''
  }
}

// 持久化当前对话（token 维度），供返回页面/刷新后恢复
function persistChat() {
  saveChatHistory({
    messages: messages.value,
    sessionId: sessionId.value,
    ctxBrandId: ctxBrandId.value,
  })
}

function clearCtx() {
  ctxBrandId.value = ''
}

function closeSocket() {
  try {
    wsRef.value?.close?.()
  } catch {
    /* ignore */
  }
  wsRef.value = null
}

function handleScroll() {
  const el = scrollEl.value
  if (!el) return
  const distance = el.scrollHeight - el.scrollTop - el.clientHeight
  atBottom.value = distance < 120
}

function scrollToBottom(force = false) {
  const el = scrollEl.value
  if (!el) return
  if (!force && !atBottom.value) return
  if (rafScrollId) cancelAnimationFrame(rafScrollId)
  rafScrollId = requestAnimationFrame(() => {
    const node = scrollEl.value
    if (node) node.scrollTop = node.scrollHeight
  })
}

// ── 流式增量：rAF 帧缓冲 ──
// 每个 WS delta 不再立即触发 Vue 更新（那会导致 MarkdownView 对全文重新正则解析+ v-html 重绘）。
// 改为累积到缓冲区，每帧最多 flush 一次，将 markdown 解析频率从"可能数百次/秒"压到 ≤60fps。
let deltaBuffer = ''
let streamRafId = null

function flushDelta() {
  streamRafId = null
  if (!deltaBuffer) return
  // 🔍 诊断：每次 rAF 刷出打日志
  console.log(`[flushDelta] flushing len=${deltaBuffer.length} streamingText_before=${streamingText.value.length}`)
  streamingText.value += deltaBuffer
  const msg = messages.value.find((item) => item.id === streamState.aiId)
  if (msg) msg.content += deltaBuffer
  deltaBuffer = ''
  scrollToBottom()
}

function appendDelta(delta) {
  if (!delta) return
  // 🔍 诊断：每次 appendDelta 调用打日志
  console.log(`[appendDelta] len=${delta.length} buffer_before=${deltaBuffer.length}`)
  deltaBuffer += delta
  // 已有待执行的帧回调则只攒数据，不重复调度（同帧内多个 delta 合并一次渲染）
  if (streamRafId) return
  streamRafId = requestAnimationFrame(flushDelta)
}

/** 手动刷空剩余缓冲区（流结束时调用，确保最后一个字符不丢失） */
function flushStreamBuffer() {
  if (streamRafId) {
    cancelAnimationFrame(streamRafId)
    streamRafId = null
  }
  flushDelta()
}

// ── 推荐卡片过滤：只保留 AI 回答文本中实际提到的产品 ──
// 后端推荐引擎独立返回产品列表（可能跨品类/数量多于文本中提到的），
// 这里用文本匹配做交集，确保"AI 推荐几个就显示几张卡片"。
const BRAND_ALIASES = {
  '李宁': ['LI-NING', 'Lining', 'lining'], 'LI-NING': ['李宁', 'Lining', 'lining'],
  '威克多': ['VICTOR', 'Victor', '胜利'], 'VICTOR': ['威克多', 'Victor', '胜利'],
  '尤尼克斯': ['YONEX', 'Yonex', 'yy'], 'YONEX': ['尤尼克斯', 'Yonex'],
  '川崎': ['KAWASAKI', 'Kawasaki'], 'KAWASAKI': ['川崎'],
}

function buildSearchTerms(product) {
  const terms = []
  const name = (product.title || product.name || '')
  const brand = (product.brand || '')

  // 完整名称
  if (name) terms.push(name.toLowerCase())

  // 名称中的型号部分（通常在空格/横线后的关键词）
  // 如 "Li-NING 战戟 6000" → 提取 "战戟 6000", "6000", "战戟"
  const parts = name.split(/[\s\-·_]+/).filter(Boolean)
  if (parts.length >= 2) {
    // 品牌后+型号：如 "战戟 6000", "极速 JS-12"
    terms.push(parts.slice(1).join(' ').toLowerCase())
    // 纯型号数字/字母：如 "6000", "JS-12"
    const lastPart = parts[parts.length - 1]
    if (/\d/.test(lastPart) || /[A-Z]{2,}/i.test(lastPart)) {
      terms.push(lastPart.toLowerCase())
    }
  }
  // 单词级别的型号（如 "BG80", "BG65", "JS-12"）
  for (const p of parts) {
    if (/[A-Z0-9]{2,}/i.test(p) && p.length >= 2) {
      terms.push(p.toLowerCase())
    }
  }

  // 品牌 + 型号组合
  if (brand && parts.length >= 1) {
    for (const alias of [...BRAND_ALIASES[brand] || [], brand]) {
      if (parts.length >= 2) {
        terms.push((alias + ' ' + parts.slice(-1)[0]).toLowerCase())
      }
      terms.push(alias.toLowerCase())
    }
  }

  return [...new Set(terms)]
}

function filterProductsByAnswer(products, answerText) {
  if (!products || !products.length || !answerText) return []
  const text = answerText.toLowerCase()

  return products.filter((p) => {
    const terms = buildSearchTerms(p)
    // 任一搜索词在文本中出现 → 该产品被 AI 提到
    for (const term of terms) {
      if (!term) continue
      // 短词（≥3 字符）精确匹配，避免 "BG6" 匹配到 "BG65"
      if (term.length >= 4 && text.includes(term)) return true
      if (term.length >= 2 && /^[A-Z0-9]+$/i.test(term) && text.includes(term)) return true
      // 中文词 ≥2 字符
      if (/[\u4e00-\u9fff]/.test(term) && term.length >= 2 && text.includes(term)) return true
    }
    return false
  })
}

// 持久化做防抖，避免流式每条增量都写 localStorage 造成主线程卡顿
let persistTimer = null
function schedulePersist(delay = 700) {
  if (persistTimer) clearTimeout(persistTimer)
  persistTimer = setTimeout(() => persistChat(), delay)
}

function appendUserMessage(text) {
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: text,
  })
}

function appendAssistantMessage() {
  const id = Date.now() + 1
  messages.value.push({
    id,
    role: 'assistant',
    content: '',
    products: [],
    sources: [],
    streaming: true,
  })
  streamState.aiId = id
  streamingText.value = ''   // 每条新回复重置流式文本
  return id
}

function retryLast() {
  if (lastQuestion.value && !loading.value) {
    inputText.value = lastQuestion.value
    askNow()
  }
}

async function askNow(preset) {
  console.log('[Chat v5] askNow 触发 — 如果看到此条说明已加载最新版代码')
  const text = String(preset ?? inputText.value ?? '').trim()
  if (!text || loading.value) return

  closeSocket()
  errorText.value = ''
  lastQuestion.value = text
  appendUserMessage(text)
  inputText.value = ''
  loading.value = true
  const aiId = appendAssistantMessage()
  scrollToBottom(true)

  let token = ''
  try {
    token = await ensureToken()
  } catch (err) {
    const reason = err?.message || String(err)
    console.error('[Chat] ensureToken 失败:', reason)
    const msg = messages.value.find((item) => item.id === aiId)
    if (msg) {
      msg.content = '认证失败：' + reason
      msg.streaming = false
    }
    errorText.value = '后端连接失败：' + reason
    loading.value = false
    scrollToBottom(true)
    return
  }

  if (!token) {
    errorText.value = '认证失败，未获取到可用 token。'
    loading.value = false
    return
  }

  wsRef.value = chatStream(text, sessionId.value, {
    onSession: (sid) => {
      sessionId.value = sid || sessionId.value
    },
    onContent: (delta) => {
      appendDelta(delta || '')
    },
    onDone: (payload) => {
      // 先刷空缓冲区（确保最后一个 rAF 帧的增量不丢失）
      flushStreamBuffer()
      streamingText.value = ''
      const msg = messages.value.find((item) => item.id === streamState.aiId)
      if (msg) {
        msg.streaming = false
        if (!msg.content && payload.answer) {
          msg.content = payload.answer
        }
        msg.sources = payload.sources || []
        const allProducts = payload.recommended_products || []
        const answerText = msg.content || payload.answer || ''
        // 过滤：只保留 AI 回答文本中实际提到的产品，确保"推荐几个显示几个"
        const filtered = filterProductsByAnswer(allProducts, answerText)
        // 兜底：如果过滤后一个都没匹配上（可能是匹配逻辑遗漏），保留原始列表
        msg.products = filtered.length > 0 ? filtered : allProducts
        console.log('[Chat] onDone: raw=', allProducts.length, 'filtered=', filtered.length,
          'answer_len=', answerText.length,
          filtered.length > 0 ? '✅ 文本匹配过滤' : '⚠️ 全量兜底（无匹配）')
      }
      loading.value = false
      scrollToBottom(true)
      schedulePersist(0)
    },
    onError: (err) => {
      flushStreamBuffer()
      streamingText.value = ''
      const msg = messages.value.find((item) => item.id === streamState.aiId)
      if (msg) {
        msg.streaming = false
        if (!msg.content) {
          msg.content = '这次没有成功拿到后端回复。'
        }
      }
      errorText.value = err?.message || '聊天服务异常，请稍后重试。'
      loading.value = false
      scrollToBottom(true)
    },
  })
}

watch(
  () => route.query.brand,
  (brand) => {
    ctxBrandId.value = brand ? String(brand) : ''
  },
  { immediate: true }
)

watch(
  () => route.query.q,
  (query) => {
    const text = String(query || '').trim()
    if (text && text !== lastQuestion.value && !loading.value) {
      inputText.value = text
      askNow(text)
    }
  }
)

// 任意对话变化（含流式增量、session、上下文品牌）都持久化，确保返回页面/刷新可恢复
watch(
  () => [messages.value, sessionId.value, ctxBrandId.value],
  () => schedulePersist(),
  { deep: true }
)

onMounted(() => {
  // 关键修复：恢复历史而非清空，避免从「装备库」等页面返回时对话丢失
  restoreChat()
  const q = route.query.q
  if (q) {
    inputText.value = String(q)
    askNow(String(q))
  }
})

onBeforeUnmount(() => {
  closeSocket()
  if (streamRafId) { cancelAnimationFrame(streamRafId); streamRafId = null }
  if (rafScrollId) cancelAnimationFrame(rafScrollId)
  if (persistTimer) clearTimeout(persistTimer)
})
</script>

<style scoped>
.chat-page {
  height: 100%;
  padding: 4px 20px 16px;
  background:
    radial-gradient(circle at 14% 0%, rgba(214, 255, 127, 0.14), transparent 24%),
    radial-gradient(circle at 100% 0%, rgba(110, 231, 249, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(249, 252, 255, 0.96), rgba(243, 248, 254, 0.94));
}

.chat-shell {
  height: 100%;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 10px;
}

.chat-header {
  max-width: 1180px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background:
    radial-gradient(circle at 0% 0%, rgba(214, 255, 127, 0.18), transparent 26%),
    radial-gradient(circle at 100% 0%, rgba(110, 231, 249, 0.20), transparent 28%),
    linear-gradient(135deg, rgba(7, 17, 31, 0.96), rgba(17, 41, 65, 0.90));
  box-shadow: 0 24px 56px rgba(8, 17, 31, 0.16);
  backdrop-filter: blur(24px) saturate(1.1);
}

.chat-header-copy {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 0 0 auto;
}

.chat-eyebrow {
  display: inline-flex;
  padding: 3px 8px;
  color: #d6ff7f;
  border: 1px solid rgba(214, 255, 127, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 10px;
  font-weight: 900;
  white-space: nowrap;
}

.chat-header h1 {
  margin: 0;
  color: #fff;
  font-size: 15px;
  line-height: 1.2;
  font-weight: 950;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.chat-header-side {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-left: auto;
}

.header-cap-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.header-cap {
  padding: 3px 9px;
  color: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 11px;
  font-weight: 850;
  white-space: nowrap;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  color: rgba(255, 255, 255, 0.76);
  border-left: 3px solid var(--bc, #6ee7f9);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 12px;
  white-space: nowrap;
}

.header-brand b {
  color: #fff;
}

.header-brand-clear,
.header-newchat,
.status-card button {
  height: 28px;
  padding: 0 10px;
  color: #fff;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  cursor: pointer;
  font-size: 12px;
  font-weight: 850;
}

.header-newchat {
  border: 1px solid rgba(214, 255, 127, 0.4);
  background: rgba(214, 255, 127, 0.16);
  color: #eaffc2;
}

.header-newchat:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-scroll {
  min-height: 0;
  overflow-y: auto;
  padding-right: 6px;
}

.chat-column {
  max-width: 980px;
  margin: 0 auto;
  display: grid;
  gap: 12px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.26s ease, transform 0.26s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.status-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(251, 191, 36, 0.18);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18px);
}

.status-card strong,
.status-card p {
  display: block;
}

.status-card strong {
  color: #881337;
  font-size: 13px;
  font-weight: 900;
}

.status-card p {
  margin: 4px 0 0;
  color: #9f1239;
  font-size: 13px;
  line-height: 1.55;
}

.status-card--error {
  background: rgba(255, 241, 242, 0.9);
}

.welcome-panel {
  padding: 12px 14px;
  border-radius: 18px;
  border: 1px solid rgba(203, 213, 225, 0.74);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 250, 255, 0.92)),
    linear-gradient(135deg, rgba(214, 255, 127, 0.08), rgba(110, 231, 249, 0.10));
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18px);
}

.welcome-copy {
  display: flex;
  align-items: center;
  gap: 10px;
}

.welcome-copy h2 {
  margin: 0 0 2px;
  color: #08111f;
  font-size: 18px;
  line-height: 1.12;
  font-weight: 950;
  letter-spacing: -0.03em;
}

.welcome-copy p {
  margin: 0;
  color: #5b6c81;
  font-size: 12px;
  line-height: 1.45;
}

.suggest-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.suggest-chip {
  min-height: 48px;
  padding: 11px 14px;
  color: #162739;
  text-align: left;
  border: 1px solid rgba(210, 223, 238, 0.9);
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.94)),
    linear-gradient(135deg, rgba(214, 255, 127, 0.08), rgba(110, 231, 249, 0.08));
  cursor: pointer;
  font-size: 13px;
  font-weight: 850;
  line-height: 1.42;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.suggest-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(110, 231, 249, 0.52);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
}

.message {
  display: grid;
  gap: 8px;
}

.message--user {
  justify-items: end;
}

.assistant-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 2px;
}

.assistant-meta-copy {
  display: grid;
  gap: 1px;
}

.assistant-meta-copy strong {
  color: #243446;
  font-size: 13px;
  font-weight: 900;
}

.assistant-meta-copy span {
  color: #7b8ca1;
  font-size: 11px;
  font-weight: 700;
}

.message-bubble {
  max-width: min(100%, 820px);
  padding: 14px 16px;
  border-radius: 18px;
  word-break: break-word;
}

.message-bubble--assistant {
  color: #0f172a;
  border-top-left-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 252, 255, 0.92)),
    linear-gradient(135deg, rgba(214, 255, 127, 0.06), rgba(110, 231, 249, 0.06));
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18px);
}

.message-bubble--user {
  max-width: min(58%, 460px);
  color: #fff;
  border-top-right-radius: 10px;
  background: linear-gradient(135deg, #0d1728, #182b44);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.14);
}

.message-plain {
  font-size: 14px;
  line-height: 1.68;
}

.reco-panel {
  max-width: 820px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(203, 213, 225, 0.74);
  background: rgba(248, 251, 255, 0.94);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
}

.reco-panel-head span,
.reco-panel-head b {
  display: block;
}

.reco-panel-head span {
  color: #0f698a;
  font-size: 11px;
  font-weight: 900;
}

.reco-panel-head b {
  margin-top: 4px;
  color: #08111f;
  font-size: 16px;
  font-weight: 950;
}

.reco-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.composer-card {
  max-width: 980px;
  margin: 0 auto;
  padding: 9px;
  border-radius: 18px;
  border: 1px solid rgba(203, 213, 225, 0.8);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.94));
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.10);
  backdrop-filter: blur(22px);
}

.composer-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 4px 6px;
}

.composer-status span {
  color: #0f172a;
  font-size: 12px;
  font-weight: 900;
}

.composer-status small {
  color: #7b8ca1;
  font-size: 11px;
}

.composer-main {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.composer-input {
  flex: 1;
  min-height: 48px;
  max-height: 120px;
  padding: 13px 14px;
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 16px;
  outline: 0;
  resize: none;
  background: rgba(255, 255, 255, 0.94);
  font-size: 14px;
  line-height: 1.5;
}

.composer-input:focus {
  border-color: rgba(110, 231, 249, 0.62);
  box-shadow: 0 0 0 4px rgba(110, 231, 249, 0.12);
}

.composer-send {
  min-width: 88px;
  height: 48px;
  color: #07111f;
  border: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, #d6ff7f 0%, #6ee7f9 54%, #ffb0c7 100%);
  box-shadow: 0 14px 30px rgba(110, 231, 249, 0.22);
  cursor: pointer;
  font-size: 14px;
  font-weight: 950;
}

.composer-send:disabled {
  opacity: 0.58;
  cursor: not-allowed;
}

@media (max-width: 1080px) {
  .chat-header {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .chat-page {
    padding: 12px 10px 12px;
  }

  .chat-header,
  .welcome-panel,
  .composer-card {
    border-radius: 16px;
  }

  .chat-header h1 {
    font-size: 20px;
  }

  .welcome-copy {
    align-items: flex-start;
  }

  .welcome-copy h2 {
    font-size: 16px;
  }

  .reco-grid {
    grid-template-columns: 1fr;
  }

  .suggest-grid {
    grid-template-columns: 1fr;
  }

  .status-card,
  .composer-status,
  .composer-main {
    flex-direction: column;
    align-items: stretch;
  }

  .message-bubble--user,
  .message-bubble,
  .reco-panel {
    max-width: 100%;
  }

  .composer-send {
    width: 100%;
  }
}
</style>
