<template>
  <div>
    <nav class="navbar navbar-dark bg-dark px-4">
      <span class="navbar-brand fw-bold">EMP — Student</span>
      <span class="text-white me-3">{{ username }}</span>
      <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
    </nav>

    <div class="container-fluid mt-3">
      <div class="row g-3 mb-4" v-if="stats">
        <div class="col-6 col-md-4" v-for="(val, key) in stats" :key="key">
          <div class="card text-center p-3 shadow-sm">
            <div class="fs-3 fw-bold text-dark">{{ val }}</div>
            <div class="small text-muted text-capitalize">{{ key.replace(/_/g,' ') }}</div>
          </div>
        </div>
      </div>

      <ul class="nav nav-tabs mb-3">
        <li class="nav-item" v-for="t in tabs" :key="t.key">
          <a class="nav-link" :class="{ active: activeTab === t.key }"
             href="#" @click.prevent="activeTab = t.key">{{ t.label }}</a>
        </li>
      </ul>

      <StudentExams v-if="activeTab === 'exams'" />
      <StudentBookings v-if="activeTab === 'bookings'" />
      <StudentResults v-if="activeTab === 'results'" />
      <StudentProfile v-if="activeTab === 'profile'" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import StudentExams from '../components/student/StudentExams.vue'
import StudentBookings from '../components/student/StudentBookings.vue'
import StudentResults from '../components/student/StudentResults.vue'
import StudentProfile from '../components/student/StudentProfile.vue'

const router = useRouter()
const username = localStorage.getItem('username')
const stats = ref(null)
const activeTab = ref('exams')
const tabs = [
  { key: 'exams', label: 'Book Exam' },
  { key: 'bookings', label: 'My Bookings' },
  { key: 'results', label: 'Results' },
  { key: 'profile', label: 'Profile' },
]

onMounted(async () => {
  try {
    const res = await api.studentDashboard()
    stats.value = res.data
  } catch {}
})

function logout() {
  localStorage.clear()
  router.push('/')
}
</script>
