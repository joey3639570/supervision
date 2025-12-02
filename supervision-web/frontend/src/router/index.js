import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/detect',
    name: 'Detection',
    component: () => import('../views/DetectionView.vue')
  },
  {
    path: '/segment',
    name: 'Segmentation',
    component: () => import('../views/SegmentationView.vue')
  },
  {
    path: '/track',
    name: 'Tracking',
    component: () => import('../views/TrackingView.vue')
  },
  {
    path: '/annotate',
    name: 'Annotation',
    component: () => import('../views/AnnotationView.vue')
  },
  {
    path: '/dataset',
    name: 'Dataset',
    component: () => import('../views/DatasetView.vue')
  },
  {
    path: '/metrics',
    name: 'Metrics',
    component: () => import('../views/MetricsView.vue')
  },
  {
    path: '/geometry',
    name: 'Geometry',
    component: () => import('../views/GeometryView.vue')
  },
  {
    path: '/video',
    name: 'Video',
    component: () => import('../views/VideoView.vue')
  },
  {
    path: '/sam3',
    name: 'SAM3',
    component: () => import('../views/SAM3View.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router



