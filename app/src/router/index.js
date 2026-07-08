import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layout/AppShell.vue'),
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', name: 'Home', component: () => import('@/views/Home.vue'), meta: { title: 'AI 选品', icon: 'spark', nav: true } },
      { path: 'brands', name: 'Brands', component: () => import('@/views/Brands.vue'), meta: { title: '装备库', icon: 'grid', nav: true } },
      { path: 'chat', name: 'Chat', component: () => import('@/views/Chat.vue'), meta: { title: 'AI 问答', icon: 'chat', nav: true } },
      { path: 'brand/:id', name: 'BrandDetail', component: () => import('@/views/BrandDetail.vue'), meta: { title: '品牌详情' } },
      { path: 'article/:id', name: 'Article', component: () => import('@/views/Article.vue'), meta: { title: '装备详情' } },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
