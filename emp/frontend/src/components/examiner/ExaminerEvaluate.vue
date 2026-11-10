<template>
  <div>
    <div class="mb-3">
      <label class="form-label fw-semibold">Select Slot</label>
      <select v-model="selectedSlotId" class="form-select w-auto" @change="loadStudents">
        <option value="">— choose a slot —</option>
        <option v-for="s in slots" :key="s.id" :value="s.id">
          Slot #{{ s.id }} | {{ s.date }} {{ s.start_time }}
        </option>
      </select>
    </div>

    <div v-if="msg" class="alert alert-success py-2">{{ msg }}</div>

    <table class="table table-bordered bg-white" v-if="students.length">
      <thead class="table-success">
        <tr><th>Student</th><th>Status</th><th>Marks</th><th>Remarks</th><th>Action</th></tr>
      </thead>
      <tbody>
        <tr v-for="st in students" :key="st.booking_id">
          <td>{{ st.student_name }}</td>
          <td>{{ st.booking_status }}</td>
          <td>
            <input v-model.number="evalForms[st.booking_id].marks" type="number" class="form-control form-control-sm"
                   style="width:80px" :disabled="st.booking_status === 'Cancelled'" />
          </td>
          <td>
            <input v-model="evalForms[st.booking_id].remarks" class="form-control form-control-sm"
                   :disabled="st.booking_status === 'Cancelled'" />
          </td>
          <td>
            <button class="btn btn-sm btn-success"
                    :disabled="st.booking_status === 'Cancelled'"
                    @click="submit(st.booking_id)">
              {{ st.evaluated ? 'Update' : 'Submit' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="selectedSlotId" class="text-muted">No students booked for this slot.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const slots = ref([])
const students = ref([])
const selectedSlotId = ref('')
const evalForms = ref({})
const msg = ref('')

onMounted(async () => {
  const res = await api.examinerSlots()
  slots.value = res.data
})

async function loadStudents() {
  if (!selectedSlotId.value) return
  const res = await api.slotStudents(selectedSlotId.value)
  students.value = res.data
  evalForms.value = {}
  for (const st of res.data) {
    evalForms.value[st.booking_id] = { marks: st.marks ?? '', remarks: '' }
  }
}

async function submit(bookingId) {
  const f = evalForms.value[bookingId]
  try {
    await api.submitEvaluation(bookingId, { total_marks: parseFloat(f.marks), remarks: f.remarks })
    msg.value = 'Evaluation saved!'
    setTimeout(() => msg.value = '', 2000)
    await loadStudents()
  } catch (e) { alert(e.response?.data?.error || 'Error') }
}
</script>
