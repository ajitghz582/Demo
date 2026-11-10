<template>
  <div>
    <nav class="navbar navbar-dark bg-primary px-4">
      <span class="navbar-brand fw-bold">EMP — Admin</span>
      <span class="text-white me-3">{{ username }}</span>
      <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
    </nav>

    <div class="container-fluid mt-3">
      <!-- Dashboard Stats -->
      <div class="row g-3 mb-4" v-if="stats">
        <div class="col-6 col-md-2" v-for="(val, key) in stats" :key="key">
          <div class="card text-center p-3 shadow-sm">
            <div class="fs-3 fw-bold text-primary">{{ val }}</div>
            <div class="small text-muted text-capitalize">{{ key }}</div>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item" v-for="t in tabs" :key="t.key">
          <a class="nav-link" :class="{ active: activeTab === t.key }"
             href="#" @click.prevent="activeTab = t.key">{{ t.label }}</a>
        </li>
      </ul>

      <AdminCourses v-if="activeTab === 'courses'" />
      <AdminExams v-if="activeTab === 'exams'" />
      <AdminExaminers v-if="activeTab === 'examiners'" />
      <AdminStudents v-if="activeTab === 'students'" />
      <AdminBookings v-if="activeTab === 'bookings'" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import AdminCourses from '../components/admin/AdminCourses.vue'
import AdminExams from '../components/admin/AdminExams.vue'
import AdminExaminers from '../components/admin/AdminExaminers.vue'
import AdminStudents from '../components/admin/AdminStudents.vue'
import AdminBookings from '../components/admin/AdminBookings.vue'

const router = useRouter()
const username = localStorage.getItem('username')
const stats = ref(null)
const activeTab = ref('courses')

const tabs = [
  { key: 'courses', label: 'Courses' },
  { key: 'exams', label: 'Examinations' },
  { key: 'examiners', label: 'Examiners' },
  { key: 'students', label: 'Students' },
  { key: 'bookings', label: 'Bookings' },
]

onMounted(async () => {
  try {
    const res = await api.adminDashboard()
    stats.value = res.data
  } catch {}
})

function logout() {
  localStorage.clear()
  router.push('/')
}
</script>
