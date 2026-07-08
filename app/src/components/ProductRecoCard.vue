<template>
  <article class="reco-card" @click="open">
    <div class="reco-media">
      <img v-if="product.image" :src="product.image" :alt="product.title" loading="lazy" />
      <div v-else class="reco-fallback">{{ product.categoryName || '装备' }}</div>

      <div class="reco-badges">
        <span class="reco-badge reco-badge--category">{{ product.categoryName || '装备' }}</span>
        <span v-if="product.brand" class="reco-badge reco-badge--brand">{{ product.brand }}</span>
      </div>
    </div>

    <div class="reco-body">
      <div class="reco-title-row">
        <div>
          <h3>{{ product.title }}</h3>
          <p class="reco-series" v-if="product.series">{{ product.series }}</p>
        </div>
        <div class="reco-score">
          <small>适配</small>
          <strong>{{ formatScore(product.score) }}</strong>
        </div>
      </div>

      <p class="reco-summary">{{ product.summary }}</p>

      <div v-if="product.specs?.length" class="reco-specs">
        <span v-for="spec in product.specs.slice(0, 4)" :key="spec">{{ spec }}</span>
      </div>

      <div class="reco-foot">
        <div class="reco-price">
          <small>参考价</small>
          <strong>{{ product.priceRange }}</strong>
        </div>

        <div v-if="product.tags?.length" class="reco-tags">
          <span v-for="tag in product.tags.slice(0, 2)" :key="tag">{{ tag }}</span>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  product: { type: Object, required: true },
})

const router = useRouter()

function open() {
  if (props.product?.id) {
    router.push(`/article/${props.product.id}`)
  }
}

function formatScore(score) {
  const value = Number(score)
  return Number.isFinite(value) ? value.toFixed(value >= 1 ? 0 : 2) : '--'
}
</script>

<style scoped>
.reco-card {
  height: 100%;
  display: grid;
  grid-template-rows: 164px 1fr;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.reco-card:hover {
  transform: translateY(-3px);
  border-color: rgba(110, 231, 249, 0.56);
  box-shadow: 0 22px 52px rgba(15, 23, 42, 0.12);
}

.reco-media {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 18%, rgba(255, 255, 255, 0.48), transparent 28%),
    linear-gradient(135deg, #0c1728, #19314d);
}

.reco-media img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.reco-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.94);
  font-size: 20px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.reco-badges {
  position: absolute;
  left: 14px;
  right: 14px;
  top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.reco-badge {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
  backdrop-filter: blur(12px);
}

.reco-badge--category {
  color: #07111f;
  background: rgba(214, 255, 127, 0.92);
}

.reco-badge--brand {
  color: #fff;
  background: rgba(7, 17, 31, 0.48);
  border: 1px solid rgba(255, 255, 255, 0.22);
}

.reco-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
}

.reco-title-row,
.reco-foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.reco-body h3,
.reco-series,
.reco-summary,
.reco-score small,
.reco-price small,
.reco-price strong {
  margin: 0;
}

.reco-body h3 {
  color: #08111f;
  font-size: 18px;
  line-height: 1.34;
  font-weight: 950;
}

.reco-series {
  margin-top: 4px;
  color: #7b8ca1;
  font-size: 12px;
  font-weight: 800;
}

.reco-summary {
  color: #56667b;
  font-size: 14px;
  line-height: 1.68;
}

.reco-specs,
.reco-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reco-specs span,
.reco-tags span {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 850;
}

.reco-specs span {
  color: #0f172a;
  background: rgba(241, 245, 249, 0.94);
}

.reco-tags span {
  color: #0f698a;
  background: rgba(224, 242, 254, 0.92);
}

.reco-score {
  text-align: right;
}

.reco-score small,
.reco-price small {
  display: block;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 800;
}

.reco-score strong,
.reco-price strong {
  display: block;
  margin-top: 4px;
  color: #08111f;
  font-size: 18px;
  font-weight: 950;
}

.reco-foot {
  margin-top: auto;
  align-items: flex-end;
}
</style>
