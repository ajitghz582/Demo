<template>
  <div>
    <div class="d-flex gap-2 mb-3 flex-wrap">
      <input v-model="search" class="form-control w-auto" placeholder="Search exams…" @input="load" />
      <select v-model="filterType" class="form-select w-auto" @change="load">
        <option value="">All Types</option>
        <option>Viva</option><option>Practical</option>
        <option>Project Demo</option><option>Assessment</option>
      </select>
    </div>

    <div v-if="msg" class="alert py-2" :class="msgType === 'success' ? 'alert-success' : 'alert-danger'">{{ msg }}</div>

    <div class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="e in exams" :key="e.id">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h6 class="card-title">{{ e.name }}</h6>
            <p class="card-text small text-muted mb-1">{{ e.course_name }} · {{ e.exam_type }}</p>
            <p class="card-text small">Duration: {{ e.duration }} min | Max: {{ e.max_marks }}</p>
            <span class="badge mb-2" :class="statusClass(e.status)">{{ e.status }}</span>
            <div v-if="e.status === 'Booking Open'">
              <button class="btn btn-sm btn-primary w-100" @click="openBooking(e)">View Slots & Book</button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-12" v-if="!exams.length">
        <p class="text-muted">No examinations available.</p>
      </div>
    </div>

    <!-- Slot Booking Modal -->
    <div v-if="bookModal.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog modal-lg"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Book Slot — {{ bookModal.examName }}</h5>
          <button class="btn-close" @click="bookModal.show=false"></button>
        </div>
        <div class="modal-body">
          <div v-if="bookMsg" class="alert py-2" :class="bookMsgType==='success'?'alert-success':'alert-danger'">{{ bookMsg }}</div>
          <table class="table table-sm">
            <thead><tr><th>Date</th><th>Time</th><th>Examiner</th><th>Seats</th><th>Link</th><th></th></tr></thead>
            <tbody>
              <tr v-for="s in bookModal.slots" :key="s.id">
                <td>{{ s.date }}</td>
                <td>{{ s.start_time }} – {{ s.end_time }}</td>
                <td>{{ s.examiner_name }}</td>
                <td>{{ s.available_seats }}</td>
                <td>
                  <a v-if="s.meeting_link" :href="s.meeting_link" target="_blank" class="small">Link</a>
                  <span v-else class="text-muted small">—</span>
                </td>
                <td>
                  <button class="btn btn-sm btn-primary" @click="book(s.id)">Book</button>
                </td>
              </tr>
              <tr v-if="!bookModal.slots.length">
                <td colspan="6" class="text-center text-muted">No available slots</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const exams = ref([])
const search = ref('')
const filterType = ref('')
const msg = ref('')
const msgType = ref('success')
const bookModal = ref({ show: false, examId: null, examName: '', slots: [] })
const bookMsg = ref('')
const bookMsgType = ref('success')

onMounted(load)

async function load() {
  const res = await api.studentExams(search.value, filterType.value)
  exams.value = res.data
}

async function openBooking(e) {
  bookMsg.value = ''
  bookModal.value = { show: true, examId: e.id, examName: e.name, slots: [] }
  try {
    const res = await api.studentSlots(e.id)
    bookModal.value.slots = res.data
  } catch (err) {
    bookMsg.value = err.response?.data?.error || 'Could not load slots'
    bookMsgType.value = 'danger'
  }
}

async function book(slotId) {
  try {
    await api.bookSlot({ slot_id: slotId })
    bookMsg.value = 'Slot booked successfully!'
    bookMsgType.value = 'success'
    const res = await api.studentSlots(bookModal.value.examId)
    bookModal.value.slots = res.data
  } catch (e) {
    bookMsg.value = e.response?.data?.error || 'Booking failed'
    bookMsgType.value = 'danger'
  }
}

function statusClass(s) {
  return { 'bg-primary': s==='Booking Open', 'bg-warning text-dark': s==='Slot Creation',
           'bg-secondary': s==='Draft', 'bg-danger': s==='Closed', 'bg-success': s==='Completed' }
}
</script>
