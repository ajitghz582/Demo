<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <button class="btn btn-success" @click="openCreate">+ Create Slot</button>
    </div>
    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-success">
        <tr><th>Exam</th><th>Date</th><th>Time</th><th>Capacity</th><th>Available</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="s in slots" :key="s.id">
          <td>{{ examName(s.exam_id) }}</td>
          <td>{{ s.date }}</td>
          <td>{{ s.start_time }} – {{ s.end_time }}</td>
          <td>{{ s.capacity }}</td>
          <td>{{ s.available_seats }}</td>
          <td><span class="badge" :class="slotClass(s.status)">{{ s.status }}</span></td>
          <td class="d-flex gap-1">
            <button class="btn btn-sm btn-outline-primary" @click="edit(s)">Edit</button>
            <button class="btn btn-sm btn-outline-info" @click="viewStudents(s)">Students ({{ s.booked_count }})</button>
            <button class="btn btn-sm btn-outline-danger" @click="remove(s.id)">Delete</button>
          </td>
        </tr>
        <tr v-if="!slots.length"><td colspan="7" class="text-center text-muted">No slots created yet</td></tr>
      </tbody>
    </table>

    <!-- Slot Form Modal -->
    <div v-if="form.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ form.id ? 'Edit' : 'Create' }} Slot</h5>
          <button class="btn-close" @click="form.show=false"></button>
        </div>
        <div class="modal-body">
          <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
          <div v-if="!form.id">
            <select v-model="form.exam_id" class="form-select mb-2">
              <option value="">Select Examination</option>
              <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.name }} ({{ e.status }})</option>
            </select>
          </div>
          <input v-model="form.date" type="date" class="form-control mb-2" />
          <input v-model="form.start_time" type="time" class="form-control mb-2" />
          <input v-model="form.end_time" type="time" class="form-control mb-2" />
          <input v-model.number="form.capacity" type="number" class="form-control mb-2" placeholder="Capacity" />
          <input v-model="form.meeting_link" class="form-control mb-2" placeholder="Meeting Link (optional)" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="form.show=false">Cancel</button>
          <button class="btn btn-success" @click="save">Save</button>
        </div>
      </div></div>
    </div>

    <!-- Students Modal -->
    <div v-if="studentsModal.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Booked Students</h5>
          <button class="btn-close" @click="studentsModal.show=false"></button>
        </div>
        <div class="modal-body">
          <table class="table table-sm">
            <thead><tr><th>Student</th><th>Email</th><th>Status</th><th>Marks</th></tr></thead>
            <tbody>
              <tr v-for="st in studentsModal.students" :key="st.booking_id">
                <td>{{ st.student_name }}</td>
                <td>{{ st.student_email }}</td>
                <td>{{ st.booking_status }}</td>
                <td>{{ st.marks ?? '—' }}</td>
              </tr>
              <tr v-if="!studentsModal.students.length">
                <td colspan="4" class="text-center text-muted">No students booked</td>
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

const slots = ref([])
const exams = ref([])
const msg = ref('')
const formError = ref('')
const form = ref({ show: false, id: null, exam_id: '', date: '', start_time: '', end_time: '', capacity: 1, meeting_link: '' })
const studentsModal = ref({ show: false, students: [] })

onMounted(async () => {
  try {
    const [sRes, eRes] = await Promise.all([api.examinerSlots(), api.examinerExams()])
    slots.value = sRes.data
    exams.value = eRes.data
    // Add booked_count to slots (api already includes it, just ensure consistent)
  } catch {}
})

async function loadSlots() {
  const [sRes, eRes] = await Promise.all([api.examinerSlots(), api.examinerExams()])
  slots.value = sRes.data
  exams.value = eRes.data
}

function examName(id) {
  return exams.value.find(e => e.id === id)?.name || `Exam #${id}`
}

function openCreate() {
  Object.assign(form.value, { show: true, id: null, exam_id: '', date: '', start_time: '', end_time: '', capacity: 1, meeting_link: '' })
  formError.value = ''
}

function edit(s) {
  Object.assign(form.value, { show: true, ...s })
  formError.value = ''
}

async function save() {
  formError.value = ''
  try {
    if (form.value.id) await api.updateSlot(form.value.id, form.value)
    else await api.createSlot(form.value)
    form.value.show = false
    msg.value = 'Saved!'
    setTimeout(() => msg.value = '', 2000)
    await loadSlots()
  } catch (e) { formError.value = e.response?.data?.error || 'Error' }
}

async function remove(id) {
  if (!confirm('Delete this slot?')) return
  try {
    await api.deleteSlot(id)
    await loadSlots()
  } catch (e) { alert(e.response?.data?.error || 'Error') }
}

async function viewStudents(s) {
  const res = await api.slotStudents(s.id)
  studentsModal.value = { show: true, students: res.data }
}

function slotClass(s) {
  return { 'bg-success': s==='Available', 'bg-danger': s==='Full',
           'bg-secondary': s==='Cancelled', 'bg-primary': s==='Completed' }
}
</script>
