<template>
  <div class="ai-mark" :style="{ '--size': `${size}px` }" :class="{ soft }" aria-hidden="true">
    <div class="ai-core">
      <img class="ai-avatar" :src="avatarSrc" alt="羽智选头像" />
    </div>
  </div>
</template>

<script setup>
import avatarSrc from '@/assets/ai-avatar.png'

defineProps({
  size: { type: Number, default: 42 },
  soft: { type: Boolean, default: false },
})
</script>

<style scoped>
.ai-mark {
  width: var(--size);
  height: var(--size);
  padding: max(2px, calc(var(--size) * 0.05));
  border-radius: calc(var(--size) * 0.32);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.22)),
    linear-gradient(135deg, rgba(214, 255, 127, 0.78), rgba(110, 231, 249, 0.86), rgba(217, 236, 255, 0.92));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.82),
    0 14px 30px rgba(19, 39, 64, 0.14);
}

.ai-mark.soft {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.86),
    0 10px 20px rgba(19, 39, 64, 0.10);
}

.ai-core {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.58);
  border-radius: calc(var(--size) * 0.26);
  background:
    radial-gradient(circle at 50% 40%, rgba(255, 255, 255, 0.9), rgba(208, 236, 255, 0.88) 58%, rgba(178, 222, 255, 0.84));
  backdrop-filter: blur(10px) saturate(1.08);
}

.ai-avatar {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: center;
  transform: scale(1.34);
  transform-origin: center;
  filter: saturate(1.08) contrast(1.06);
}
</style>
