<template>
  <div class="page home-page">
    <section class="hero fade-up">
      <div class="hero-copy">
        <div class="hero-tag">RAG AI · 羽毛球装备选品</div>
        <h1>把预算、打法和水平告诉 AI</h1>
        <p>从管理员维护的装备库里对比球拍、球线、羽毛球和球鞋。价格只作为预算参考，不做交易系统。</p>

        <div class="hero-ask">
          <input v-model="quickQuestion" placeholder="例如：预算 600，双打新手，球拍怎么选？" @keyup.enter="ask" />
          <button @click="ask">问 AI</button>
        </div>

        <div class="hero-actions">
          <button class="btn-primary" @click="go('/chat')">打开 AI 问答</button>
          <button class="btn-ghost" @click="go('/brands')">浏览装备库</button>
        </div>
      </div>

      <div class="hero-visual" aria-hidden="true">
        <div class="athlete-photo">
          <img src="/assets/hero/lin-dan-smash.png" alt="" />
          <div class="photo-glass">
            <span>Smash Mode</span>
            <b>从实战打法反推装备</b>
            <small>进攻、防守、速度、预算，一次对比</small>
          </div>
        </div>
      </div>
    </section>

    <div class="category-strip">
      <button v-for="c in categories" :key="c.id" class="category-card" @click="openCategory(c.id)">
        <span>{{ c.icon }}</span>
        <b>{{ c.name }}</b>
        <small>{{ c.desc }}</small>
      </button>
    </div>

    <div class="section-head">
      <h2>热门品牌</h2>
      <span class="sub" @click="go('/brands')">查看全部 ›</span>
    </div>

    <div class="brand-grid">
      <button
        v-for="(b, i) in brands"
        :key="b.id"
        class="brand-card fade-up"
        :style="{ animationDelay: i * 40 + 'ms' }"
        @click="openBrand(b)"
      >
        <span class="brand-logo">
          <img :src="b.logo" :alt="`${b.name} logo`" loading="lazy" />
        </span>
        <span class="brand-name">{{ b.nameCn }}</span>
        <span class="brand-en">{{ b.name }}</span>
        <span class="brand-tags">
          <span v-for="t in b.tags" :key="t">{{ t }}</span>
        </span>
      </button>
    </div>

    <div class="section-head">
      <h2>AI 常问对比</h2>
      <span class="sub">预算和价格只用于辅助比较</span>
    </div>
    <div class="qa-chips">
      <button v-for="q in hot" :key="q" class="qa-chip" @click="ask(q)">{{ q }}</button>
    </div>

    <div class="section-head">
      <h2>热门装备条目</h2>
      <span class="sub">来自后台装备数据库</span>
    </div>
    <div class="kb-grid">
      <div v-for="(a, i) in featured" :key="a.id" class="fade-up" :style="{ animationDelay: i * 50 + 'ms' }">
        <KnowledgeCard :article="a" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { brands, categories } from '@/data/knowledge'
import { fetchProducts } from '@/api/product'
import KnowledgeCard from '@/components/KnowledgeCard.vue'

defineOptions({ name: 'Home' })

const router = useRouter()
const quickQuestion = ref('')
const products = ref([])
const featured = computed(() => products.value.slice(0, 8))
const hot = [
  '预算 600 元，新手球拍怎么选？',
  '双打速度型球拍怎么对比？',
  '球线耐打和高弹怎么选？',
  '宽脚羽毛球鞋推荐看什么？',
  '训练用羽毛球怎么选？',
]

function go(p) {
  router.push(p)
}

function openBrand(b) {
  router.push(`/brand/${b.id}`)
}

function openCategory(category) {
  router.push(`/brands?category=${category}`)
}

function ask(preset) {
  const text = typeof preset === 'string' ? preset : quickQuestion.value.trim()
  router.push(`/chat${text ? `?q=${encodeURIComponent(text)}` : ''}`)
}

onMounted(async () => {
  const res = await fetchProducts()
  products.value = res.list
})
</script>

<style scoped>
.home-page {
  padding-top: 18px;
}

.hero {
  position: relative;
  min-height: 420px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.82fr);
  gap: 30px;
  overflow: hidden;
  padding: 42px;
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: 34px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(236, 254, 255, 0.74)),
    linear-gradient(120deg, rgba(217, 249, 157, 0.35), rgba(103, 232, 249, 0.2), rgba(253, 164, 175, 0.2));
  box-shadow: var(--shadow-lg);
}

.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(115deg, transparent 0 58%, rgba(15, 23, 42, 0.04) 58% 61%, transparent 61%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), transparent);
  pointer-events: none;
}

.hero-copy,
.hero-visual {
  position: relative;
  z-index: 1;
}

.hero-tag {
  display: inline-flex;
  margin-bottom: 18px;
  padding: 8px 14px;
  color: #0f766e;
  border: 1px solid rgba(15, 118, 110, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 950;
}

.hero h1 {
  max-width: 650px;
  margin: 0;
  color: #08111f;
  font-size: 56px;
  line-height: 1.02;
  font-weight: 950;
  letter-spacing: 0;
}

.hero p {
  max-width: 560px;
  margin: 18px 0 24px;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.8;
}

.hero-ask {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 620px;
  padding: 8px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-sm);
}

.hero-ask input {
  flex: 1;
  min-width: 0;
  height: 40px;
  padding: 0 12px;
  color: var(--text-primary);
  border: 0;
  outline: 0;
  background: transparent;
}

.hero-ask button {
  height: 40px;
  padding: 0 18px;
  color: #07111f;
  border: 0;
  border-radius: 999px;
  background: var(--sport-gradient);
  cursor: pointer;
  font-weight: 950;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px;
}

.hero-actions .btn-ghost {
  color: var(--text-primary);
  border-color: rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.68);
}

.hero-visual {
  min-height: 336px;
}

.athlete-photo {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 32px;
  background: #07111f;
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.18);
}

.athlete-photo::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(7, 17, 31, 0.52), transparent 48%),
    linear-gradient(0deg, rgba(7, 17, 31, 0.36), transparent 58%);
  pointer-events: none;
}

.athlete-photo img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: 54% 50%;
}

.photo-glass {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 20px;
  z-index: 1;
  padding: 16px 18px;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 22px;
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(18px);
}

.photo-glass span,
.photo-glass b,
.photo-glass small {
  display: block;
}

.photo-glass span {
  color: #d9f99d;
  font-size: 11px;
  font-weight: 950;
}

.photo-glass b {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 950;
}

.photo-glass small {
  margin-top: 5px;
  color: rgba(255, 255, 255, 0.72);
}

.category-strip,
.brand-grid,
.kb-grid {
  display: grid;
  gap: 16px;
}

.category-strip {
  grid-template-columns: repeat(4, 1fr);
  margin-top: 18px;
}

.category-card,
.brand-card,
.qa-chip {
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(16px);
}

.category-card {
  min-height: 132px;
  padding: 18px;
  text-align: left;
  border-radius: 24px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.category-card:hover,
.brand-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.category-card span,
.category-card b,
.category-card small {
  display: block;
}

.category-card span {
  font-size: 24px;
}

.category-card b {
  margin-top: 12px;
  font-size: 18px;
  font-weight: 950;
}

.category-card small {
  margin-top: 8px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.brand-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.brand-card {
  min-height: 202px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18px 14px;
  text-align: center;
  border-radius: 26px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.brand-logo {
  width: 132px;
  height: 62px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

.brand-logo img {
  max-width: 132px;
  max-height: 62px;
  display: block;
  object-fit: contain;
}

.brand-name {
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 950;
}

.brand-en {
  margin-top: 2px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.brand-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.brand-tags span {
  padding: 3px 8px;
  color: var(--primary-2);
  border-radius: 999px;
  background: var(--primary-light);
  font-size: 11px;
  font-weight: 850;
}

.qa-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.qa-chip {
  padding: 11px 17px;
  color: var(--text-secondary);
  border-radius: 999px;
  font-weight: 800;
  transition: transform 0.16s ease, background 0.16s ease;
}

.qa-chip:hover {
  transform: translateY(-2px);
  color: #07111f;
  background: var(--sport-gradient);
}

.kb-grid {
  grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 1180px) {
  .brand-grid,
  .kb-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 960px) {
  .hero,
  .category-strip {
    grid-template-columns: 1fr;
  }

  .hero-visual {
    min-height: 320px;
  }
}

@media (max-width: 760px) {
  .hero {
    padding: 24px 18px;
    border-radius: 26px;
  }

  .hero h1 {
    font-size: 36px;
  }

  .hero-ask {
    align-items: stretch;
    flex-direction: column;
    border-radius: 24px;
  }

  .brand-grid,
  .kb-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
