<template>
  <div class="chat-page">
    <div class="chat-shell">
      <section class="chat-header">
        <div class="chat-header-copy">
          <span class="chat-eyebrow">羽智选 · RAG AI 装备顾问</span>
          <h1>把预算、打法和具体型号直接说出来</h1>
          <p>优先按真实知识库和结构化装备库回答。型号没收录会明确告诉你，不再用本地演示数据偷偷兜底。</p>
        </div>

        <div class="chat-header-side">
          <div class="header-cap-grid">
            <span v-for="item in headerCaps" :key="item" class="header-cap">{{ item }}</span>
          </div>

          <div v-if="ctxBrand" class="header-brand" :style="{ '--bc': ctxBrand.color }">
            <span>当前优先参考 <b>{{ ctxBrand.nameCn }}</b> 装备库</span>
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
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getBrand } from '@/data/knowledge'
import { ensureToken, chatStream } from '@/api/chat'
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
  buffer: '',
  timer: null,
})

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
  messages.value = []
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
  nextTick(() => {
    const el = scrollEl.value
    if (!el) return
    if (force || atBottom.value) {
      el.scrollTop = el.scrollHeight
    }
  })
}

function flushStream(force = false) {
  if (!streamState.aiId) return
  if (!streamState.buffer && !force) return
  const msg = messages.value.find((item) => item.id === streamState.aiId)
  if (!msg) return
  if (streamState.buffer) {
    msg.content += streamState.buffer
    streamState.buffer = ''
  }
  if (streamState.timer) {
    clearTimeout(streamState.timer)
    streamState.timer = null
  }
  scrollToBottom()
}

function scheduleFlush() {
  if (streamState.timer) return
  streamState.timer = setTimeout(() => flushStream(), 48)
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
  return id
}

function retryLast() {
  if (lastQuestion.value && !loading.value) {
    inputText.value = lastQuestion.value
    askNow()
  }
}

async function askNow(preset) {
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
  } catch {
    const msg = messages.value.find((item) => item.id === aiId)
    if (msg) {
      msg.content = '当前无法连接后端 AI 服务，请确认后端已经启动，并且匿名登录接口可用。'
      msg.streaming = false
    }
    errorText.value = '后端连接失败，前台不会再偷偷降级到本地假知识库。你现在看到的是真实错误态。'
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
      streamState.buffer += delta || ''
      scheduleFlush()
    },
    onDone: (payload) => {
      flushStream(true)
      const msg = messages.value.find((item) => item.id === aiId)
      if (msg) {
        msg.streaming = false
        if (!msg.content && payload.answer) {
          msg.content = payload.answer
        }
        msg.sources = payload.sources || []
        msg.products = payload.recommended_products || []
      }
      loading.value = false
      scrollToBottom(true)
    },
    onError: (err) => {
      flushStream(true)
      const msg = messages.value.find((item) => item.id === aiId)
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

onMounted(() => {
  resetChat()
  const q = route.query.q
  if (q) {
    inputText.value = String(q)
    askNow(String(q))
  }
})

onBeforeUnmount(() => {
  closeSocket()
  if (streamState.timer) {
    clearTimeout(streamState.timer)
  }
})
</script>

<style scoped>
.chat-page {
  height: 100%;
  padding: 14px 20px 16px;
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background:
    radial-gradient(circle at 0% 0%, rgba(214, 255, 127, 0.18), transparent 26%),
    radial-gradient(circle at 100% 0%, rgba(110, 231, 249, 0.20), transparent 28%),
    linear-gradient(135deg, rgba(7, 17, 31, 0.96), rgba(17, 41, 65, 0.90));
  box-shadow: 0 24px 56px rgba(8, 17, 31, 0.16);
  backdrop-filter: blur(24px) saturate(1.1);
}

.chat-eyebrow {
  display: inline-flex;
  padding: 4px 9px;
  color: #d6ff7f;
  border: 1px solid rgba(214, 255, 127, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 11px;
  font-weight: 900;
}

.chat-header h1 {
  margin: 7px 0 5px;
  color: #fff;
  font-size: 22px;
  line-height: 1.12;
  font-weight: 950;
  letter-spacing: -0.03em;
}

.chat-header p {
  max-width: 700px;
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  line-height: 1.55;
}

.chat-header-side {
  display: grid;
  gap: 8px;
  align-content: start;
}

.header-cap-grid {
  display: grid;
  gap: 7px;
}

.header-cap {
  padding: 7px 10px;
  color: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 11px;
  font-weight: 850;
}

.header-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 10px;
  color: rgba(255, 255, 255, 0.76);
  border-left: 4px solid var(--bc, #6ee7f9);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 12px;
}

.header-brand b {
  color: #fff;
}

.header-brand-clear,
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
