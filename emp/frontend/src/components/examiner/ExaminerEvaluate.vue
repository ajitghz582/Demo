<template>
  <div>
    <!-- Slot selector -->
    <div class="mb-3">
      <label class="form-label fw-semibold">Select Slot</label>
      <select v-model="selectedSlotId" class="form-select w-auto" @change="loadStudents">
        <option value="">— choose a slot —</option>
        <option v-for="s in slots" :key="s.id" :value="s.id">
          Slot #{{ s.id }} | {{ s.date }} {{ s.start_time }}
        </option>
      </select>
    </div>

    <!-- Student selector -->
    <div class="mb-3" v-if="students.length">
      <label class="form-label fw-semibold">Select Student</label>
      <select v-model="selectedBookingId" class="form-select w-auto" @change="loadRubrics">
        <option value="">— choose a student —</option>
        <option v-for="st in students" :key="st.booking_id" :value="st.booking_id"
                :disabled="st.booking_status === 'Cancelled'">
          {{ st.student_name }} ({{ st.booking_status }})
        </option>
      </select>
    </div>
    <p v-else-if="selectedSlotId" class="text-muted">No students booked for this slot.</p>

    <!-- Rubric evaluation form -->
    <div v-if="selectedBookingId && rubrics.length" class="card shadow-sm p-3">
      <div class="mb-2 text-muted small">
        Slot #{{ selectedSlotId }} &nbsp;|&nbsp;
        Student: <strong>{{ selectedStudent?.student_name }}</strong>
      </div>

      <div v-if="msg" class="alert alert-success py-2">{{ msg }}</div>
      <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

      <table class="table table-bordered table-sm mb-3">
        <thead class="table-success">
          <tr>
            <th>Criterion</th>
            <th>Description</th>
            <th>Max Marks</th>
            <th>Awarded Marks</th>
            <th>Save</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rubrics" :key="r.rubric_id">
            <td>{{ r.criterion_name }}</td>
            <td class="text-muted small">{{ r.description || '—' }}</td>
            <td class="text-center">{{ r.max_marks }}</td>
            <td>
              <input
                v-model.number="criterionScores[r.rubric_id]"
                type="number" min="0" :max="r.max_marks" step="0.5"
                class="form-control form-control-sm"
                style="width:90px"
              />
            </td>
            <td>
              <button class="btn btn-sm btn-outline-primary" @click="saveCriterion(r)">
                Save
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="table-light fw-semibold">
            <td colspan="3" class="text-end">Total</td>
            <td class="text-center">{{ computedTotal }}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>

      <div class="mb-3">
        <label class="form-label fw-semibold">Remarks</label>
        <textarea v-model="remarks" class="form-control" rows="2" placeholder="Overall remarks…"></textarea>
      </div>

      <button class="btn btn-success" @click="submitEvaluation">Submit Evaluation</button>
    </div>

    <div v-else-if="selectedBookingId && !rubrics.length" class="alert alert-warning">
      No rubric criteria defined for this exam. Use the simple evaluation below.
      <div class="mt-2 d-flex gap-2 align-items-center">
        <input v-model.number="manualMarks" type="number" class="form-control w-auto" placeholder="Total marks" />
        <button class="btn btn-success" @click="submitSimple">Submit</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../../api.js'

const props = defineProps({ prefillSlotId: { type: [Number, String], default: null } })

const slots = ref([])
const students = ref([])
const rubrics = ref([])
const selectedSlotId = ref('')
const selectedBookingId = ref('')
const criterionScores = ref({})
const remarks = ref('')
const manualMarks = ref(0)
const msg = ref('')
const error = ref('')

const selectedStudent = computed(() =>
  students.value.find(s => s.booking_id === selectedBookingId.value)
)

const computedTotal = computed(() =>
  rubrics.value.reduce((sum, r) => sum + (Number(criterionScores.value[r.rubric_id]) || 0), 0)
)

onMounted(async () => {
  const res = await api.examinerSlots()
  slots.value = res.data
  if (props.prefillSlotId) {
    selectedSlotId.value = props.prefillSlotId
    await loadStudents()
  }
})

async function loadStudents() {
  selectedBookingId.value = ''
  rubrics.value = []
  criterionScores.value = {}
  remarks.value = ''
  if (!selectedSlotId.value) return
  const res = await api.slotStudents(selectedSlotId.value)
  students.value = res.data
}

async function loadRubrics() {
  rubrics.value = []
  criterionScores.value = {}
  remarks.value = ''
  if (!selectedBookingId.value) return
  try {
    const res = await api.getBookingRubrics(selectedBookingId.value)
    rubrics.value = res.data.rubrics
    remarks.value = res.data.remarks || ''
    for (const r of res.data.rubrics) {
      criterionScores.value[r.rubric_id] = r.awarded_marks
    }
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to load rubrics'
  }
}

async function saveCriterion(rubric) {
  msg.value = ''
  error.value = ''
  const awarded = Number(criterionScores.value[rubric.rubric_id]) || 0
  if (awarded > rubric.max_marks) {
    error.value = `"${rubric.criterion_name}" cannot exceed ${rubric.max_marks} marks`
    return
  }
  try {
    await api.saveCriterionScore(selectedBookingId.value, {
      rubric_id: rubric.rubric_id,
      awarded_marks: awarded,
    })
    msg.value = `Saved: ${rubric.criterion_name}`
    setTimeout(() => msg.value = '', 2000)
  } catch (e) {
    error.value = e.response?.data?.error || 'Error saving score'
  }
}

async function submitEvaluation() {
  msg.value = ''
  error.value = ''
  try {
    const res = await api.submitEvaluation(selectedBookingId.value, { remarks: remarks.value })
    msg.value = `Evaluation submitted — Total: ${res.data.total_marks} marks`
    await loadStudents()
    selectedBookingId.value = ''
    rubrics.value = []
  } catch (e) {
    error.value = e.response?.data?.error || 'Error submitting evaluation'
  }
}

async function submitSimple() {
  msg.value = ''
  error.value = ''
  try {
    const res = await api.submitEvaluation(selectedBookingId.value, {
      total_marks: manualMarks.value,
      remarks: remarks.value,
    })
    msg.value = `Evaluation submitted — Total: ${res.data.total_marks} marks`
    await loadStudents()
    selectedBookingId.value = ''
  } catch (e) {
    error.value = e.response?.data?.error || 'Error'
  }
}
</script>
