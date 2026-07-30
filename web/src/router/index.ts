import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'tasks',
          name: 'tasks',
          component: () => import('@/views/TaskListView.vue'),
        },
        {
          path: 'tasks/create',
          name: 'task-create',
          component: () => import('@/views/TaskCreateView.vue'),
        },
        {
          path: 'tasks/:taskNo',
          name: 'task-detail',
          component: () => import('@/views/TaskDetailView.vue'),
        },
        {
          path: 'orders',
          name: 'orders',
          component: () => import('@/views/OrdersView.vue'),
        },
        {
          path: 'products',
          name: 'products',
          component: () => import('@/views/ProductsView.vue'),
        },
        {
          path: 'bills',
          name: 'bills',
          component: () => import('@/views/BillsView.vue'),
        },
        {
          path: 'notices',
          name: 'notices',
          component: () => import('@/views/NoticesView.vue'),
        },
        {
          path: 'notices/:noticeId',
          name: 'notice-detail',
          component: () => import('@/views/NoticeDetailView.vue'),
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/UsersView.vue'),
          meta: { roles: ['admin'] },
        },
        {
          path: 'account',
          name: 'account',
          component: () => import('@/views/AccountView.vue'),
        },
        {
          path: 'system',
          name: 'system',
          component: () => import('@/views/SystemView.vue'),
          meta: { roles: ['admin'] },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach(async (to) => {
  const user = useUserStore()
  if (!to.meta.public && !user.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && user.token) {
    return { name: 'dashboard' }
  }
  // 每次有 token 都拉 /auth/me，避免降级/停用后本地 role 撒谎
  if (user.token && !to.meta.public) {
    try {
      await user.refreshMe()
    } catch {
      user.logout()
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }
  const roles = to.meta.roles as string[] | undefined
  if (roles?.length && !roles.includes(user.role)) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
