<template>
  <div>
    <div class="d-flex justify-content-between mb-3">
      <h5 class="mb-0">My Bookings</h5>
      <button class="btn btn-outline-secondary btn-sm" @click="exportHistory">Export History (Email)</button>
    </div>
    <div v-if="msg" class="alert py-2" :class="msgType==='success'?'alert-success':'alert-danger'">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-dark">
        <tr><th>Exam</th><th>Course</th><th>Date & Time</th><th>Examiner</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="b in bookings" :key="b.id">
          <td>{{ b.exam_name }}</td>
          <td>{{ b.course }}</td>
          <td>{{ b.date }} {{ b.start_time }}</td>
          <td>{{ b.examiner }}</td>
          <td><span class="badge" :class="statusClass(b.status)">{{ b.status }}</span></td>
          <td>
            <button v-if="b.status === 'Booked'" class="btn btn-sm btn-outline-danger"
                    @click="cancel(b.id)">Cancel</button>
          </td>
        </tr>
        <tr v-if="!bookings.length"><td colspan="6" class="text-center text-muted">No bookings yet</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const bookings = ref([])
const msg = ref('')
const msgType = ref('success')

onMounted(load)

async function load() {
  const res = await api.getMyBookings()
  bookings.value = res.data
}

async function cancel(id) {
  if (!confirm('Cancel this booking?')) return
  try {
    await api.cancelBooking(id)
    msg.value = 'Booking cancelled'
    msgType.value = 'success'
    await load()
  } catch (e) {
    msg.value = e.response?.data?.error || 'Error'
    msgType.value = 'danger'
  }
  setTimeout(() => msg.value = '', 3000)
}

async function exportHistory() {
  try {
    await api.exportHistory()
    msg.value = 'Export started — check your email shortly!'
    msgType.value = 'success'
  } catch (e) {
    msg.value = e.response?.data?.error || 'Export failed'
    msgType.value = 'danger'
  }
  setTimeout(() => msg.value = '', 4000)
}

function statusClass(s) {
  return { 'bg-primary': s==='Booked', 'bg-danger': s==='Cancelled', 'bg-success': s==='Completed' }
}
</script>
