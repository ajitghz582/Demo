<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <input v-model="search" class="form-control w-auto" placeholder="Search by student or exam…" @input="load" />
    </div>
    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-primary">
        <tr><th>Student</th><th>Exam</th><th>Course</th><th>Date</th><th>Examiner</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="b in bookings" :key="b.id">
          <td>{{ b.student_name }}</td>
          <td>{{ b.exam_name }}</td>
          <td>{{ b.course }}</td>
          <td>{{ b.date }} {{ b.start_time }}</td>
          <td>{{ b.examiner }}</td>
          <td><span class="badge" :class="statusClass(b.status)">{{ b.status }}</span></td>
          <td class="d-flex gap-1">
            <button class="btn btn-sm btn-outline-primary" @click="openReschedule(b)">Reschedule</button>
            <button class="btn btn-sm btn-outline-warning" @click="openReassign(b)">Reassign</button>
          </td>
        </tr>
        <tr v-if="!bookings.length"><td colspan="7" class="text-center text-muted">No bookings</td></tr>
      </tbody>
    </table>

    <!-- Reschedule Modal -->
    <div v-if="reschedule.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Reschedule Booking</h5>
          <button class="btn-close" @click="reschedule.show=false"></button>
        </div>
        <div class="modal-body">
          <p>Student: <strong>{{ reschedule.studentName }}</strong></p>
          <label class="form-label">New Slot ID</label>
          <input v-model="reschedule.newSlotId" class="form-control" type="number" placeholder="Slot ID" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="reschedule.show=false">Cancel</button>
          <button class="btn btn-primary" @click="doReschedule">Confirm</button>
        </div>
      </div></div>
    </div>

    <!-- Reassign Examiner Modal -->
    <div v-if="reassign.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Reassign Examiner</h5>
          <button class="btn-close" @click="reassign.show=false"></button>
        </div>
        <div class="modal-body">
          <select v-model="reassign.examinerId" class="form-select">
            <option value="">Select Examiner</option>
            <option v-for="e in examiners" :key="e.id" :value="e.id">{{ e.username }}</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="reassign.show=false">Cancel</button>
          <button class="btn btn-primary" @click="doReassign">Confirm</button>
        </div>
      </div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const bookings = ref([])
const examiners = ref([])
const search = ref('')
const msg = ref('')
const reschedule = ref({ show: false, bookingId: null, studentName: '', newSlotId: '' })
const reassign = ref({ show: false, bookingId: null, examinerId: '' })

onMounted(async () => {
  await load()
  const res = await api.getExaminers()
  examiners.value = res.data
})

async function load() {
  const res = await api.getAdminBookings(search.value)
  bookings.value = res.data
}

function openReschedule(b) {
  Object.assign(reschedule.value, { show: true, bookingId: b.id, studentName: b.student_name, newSlotId: '' })
}

async function doReschedule() {
  try {
    await api.rescheduleBooking(reschedule.value.bookingId, { new_slot_id: parseInt(reschedule.value.newSlotId) })
    reschedule.value.show = false
    msg.value = 'Rescheduled!'
    setTimeout(() => msg.value = '', 2000)
    await load()
  } catch (e) { alert(e.response?.data?.error || 'Error') }
}

function openReassign(b) {
  Object.assign(reassign.value, { show: true, bookingId: b.id, examinerId: '' })
}

async function doReassign() {
  try {
    await api.reassignExaminer(reassign.value.bookingId, { examiner_id: parseInt(reassign.value.examinerId) })
    reassign.value.show = false
    msg.value = 'Examiner reassigned!'
    setTimeout(() => msg.value = '', 2000)
    await load()
  } catch (e) { alert(e.response?.data?.error || 'Error') }
}

function statusClass(s) {
  return { 'bg-primary': s==='Booked', 'bg-danger': s==='Cancelled', 'bg-success': s==='Completed' }
}
</script>
