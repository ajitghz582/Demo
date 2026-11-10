import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AdminView from '../views/AdminView.vue'
import ExaminerView from '../views/ExaminerView.vue'
import StudentView from '../views/StudentView.vue'

const routes = [
  { path: '/', component: LandingPage },
  {
    path: '/admin',
    component: AdminView,
    beforeEnter: (to, from, next) => {
      if (localStorage.getItem('role') === 'admin') next()
      else next('/')
    }
  },
  {
    path: '/examiner',
    component: ExaminerView,
    beforeEnter: (to, from, next) => {
      if (localStorage.getItem('role') === 'examiner') next()
      else next('/')
    }
  },
  {
    path: '/student',
    component: StudentView,
    beforeEnter: (to, from, next) => {
      if (localStorage.getItem('role') === 'student') next()
      else next('/')
    }
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export default createRouter({ history: createWebHistory(), routes })
