import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layout/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '数据看板' } },
      { path: 'product', name: 'Product', component: () => import('@/views/Product.vue'), meta: { title: '装备管理' } },
      { path: 'category', name: 'Category', component: () => import('@/views/Category.vue'), meta: { title: '品类管理' } },
      { path: 'user', name: 'User', component: () => import('@/views/User.vue'), meta: { title: '用户管理' } },
      { path: 'banner', name: 'Banner', component: () => import('@/views/Banner.vue'), meta: { title: '内容位管理' } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('@/views/Knowledge.vue'), meta: { title: '知识库管理' } },
      { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue'), meta: { title: '个人中心' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 羽智选` : '羽智选'
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.isLoggedIn()) {
    next('/login')
  } else if (to.path === '/login' && auth.isLoggedIn()) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
