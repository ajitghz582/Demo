<template>
  <div>
    <nav class="navbar navbar-dark bg-success px-4">
      <span class="navbar-brand fw-bold">EMP — Examiner</span>
      <span class="text-white me-3">{{ username }}</span>
      <button class="btn btn-outline-light btn-sm" @click="logout">Logout</button>
    </nav>

    <div class="container-fluid mt-3">
      <div class="row g-3 mb-4" v-if="stats">
        <div class="col-6 col-md-3" v-for="(val, key) in stats" :key="key">
          <div class="card text-center p-3 shadow-sm">
            <div class="fs-3 fw-bold text-success">{{ val }}</div>
            <div class="small text-muted text-capitalize">{{ key.replace(/_/g,' ') }}</div>
          </div>
        </div>
      </div>

      <ul class="nav nav-tabs mb-3">
        <li class="nav-item" v-for="t in tabs" :key="t.key">
          <a class="nav-link" :class="{ active: activeTab === t.key }"
             href="#" @click.prevent="switchTab(t.key)">{{ t.label }}</a>
        </li>
      </ul>

      <ExaminerAssignedExams
        v-if="activeTab === 'assigned'"
        @create-slot="goCreateSlot"
      />
      <ExaminerSlots
        v-if="activeTab === 'slots'"
        :prefill-exam="prefillExam"
        @slot-created="prefillExam = null"
        @go-marking="goMarking"
      />
      <ExaminerEvaluate
        v-if="activeTab === 'evaluate'"
        :prefill-slot-id="prefillSlotId"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'
import ExaminerAssignedExams from '../components/examiner/ExaminerAssignedExams.vue'
import ExaminerSlots from '../components/examiner/ExaminerSlots.vue'
import ExaminerEvaluate from '../components/examiner/ExaminerEvaluate.vue'

const router = useRouter()
const username = localStorage.getItem('username')
const stats = ref(null)
const activeTab = ref('assigned')
const prefillExam = ref(null)
const prefillSlotId = ref(null)

const tabs = [
  { key: 'assigned', label: 'Assigned Exams' },
  { key: 'slots', label: 'My Slots' },
  { key: 'evaluate', label: 'Evaluate Students' },
]

onMounted(async () => {
  try {
    const res = await api.examinerDashboard()
    stats.value = res.data
  } catch {}
})

function switchTab(key) {
  // Clear prefill state when user navigates manually (not via a shortcut button)
  if (key !== 'slots') prefillExam.value = null
  if (key !== 'evaluate') prefillSlotId.value = null
  activeTab.value = key
}

function goCreateSlot(exam) {
  prefillExam.value = exam
  activeTab.value = 'slots'
}

function goMarking(slotId) {
  prefillSlotId.value = slotId
  activeTab.value = 'evaluate'
}

function logout() {
  localStorage.clear()
  router.push('/')
}
</script>
