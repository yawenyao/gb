import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: () => import('../views/HomeView.vue'), meta: { title: '首页' } },
    { path: '/additives', name: 'Additives', component: () => import('../views/AdditivesView.vue'), meta: { title: '食品添加剂查询' } },
    { path: '/additives/:faid', name: 'AdditiveDetail', component: () => import('../views/AdditiveDetailView.vue'), meta: { title: '添加剂详情' } },
    { path: '/categories', name: 'Categories', component: () => import('../views/CategoriesView.vue'), meta: { title: '按食品名称查询' } },
    { path: '/categories/:code', name: 'CategoryDetail', component: () => import('../views/CategoryDetailView.vue'), meta: { title: '分类使用详情' } },
    { path: '/processing-aids', name: 'ProcessingAids', component: () => import('../views/ProcessingAidsView.vue'), meta: { title: '加工助剂查询' } },
    { path: '/enzymes', name: 'Enzymes', component: () => import('../views/EnzymesView.vue'), meta: { title: '酶制剂查询' } },
    { path: '/spices', name: 'Spices', component: () => import('../views/SpicesView.vue'), meta: { title: '香精香料查询' } },
    { path: '/appendix-d', name: 'AppendixD', component: () => import('../views/AppendixDView.vue'), meta: { title: '附录D 功能类别定义' } },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || 'GB 2760 综合查询'
  document.title = `${title} - GB 2760 食品添加剂使用标准`
})

export default router
