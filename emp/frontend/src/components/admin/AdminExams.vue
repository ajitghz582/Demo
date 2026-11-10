<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <input v-model="search" class="form-control w-auto" placeholder="Search exams…" @input="load" />
      <button class="btn btn-primary" @click="openCreate">+ New Examination</button>
    </div>
    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-primary">
        <tr><th>Name</th><th>Course</th><th>Type</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="e in exams" :key="e.id">
          <td>{{ e.name }}</td>
          <td>{{ e.course_name }}</td>
          <td>{{ e.exam_type }}</td>
          <td><span class="badge" :class="statusClass(e.status)">{{ e.status }}</span></td>
          <td class="d-flex gap-1 flex-wrap">
            <button class="btn btn-sm btn-outline-primary" @click="edit(e)">Edit</button>
            <button class="btn btn-sm btn-outline-secondary" @click="manageRubrics(e)">Rubrics</button>
            <button class="btn btn-sm btn-outline-success" @click="publish(e.id)">Publish</button>
            <button class="btn btn-sm btn-outline-danger" @click="remove(e.id)">Delete</button>
          </td>
        </tr>
        <tr v-if="!exams.length"><td colspan="5" class="text-center text-muted">No examinations found</td></tr>
      </tbody>
    </table>

    <!-- Exam Form Modal -->
    <div v-if="form.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog modal-lg"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ form.id ? 'Edit' : 'New' }} Examination</h5>
          <button class="btn-close" @click="form.show=false"></button>
        </div>
        <div class="modal-body">
          <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
          <div class="row g-2">
            <div class="col-md-8"><input v-model="form.name" class="form-control" placeholder="Exam Name" /></div>
            <div class="col-md-4">
              <select v-model="form.course_id" class="form-select">
                <option value="">Select Course</option>
                <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.course_name }}</option>
              </select>
            </div>
            <div class="col-md-4">
              <select v-model="form.exam_type" class="form-select">
                <option value="">Type</option>
                <option>Viva</option><option>Practical</option>
                <option>Project Demo</option><option>Assessment</option>
              </select>
            </div>
            <div class="col-md-4"><input v-model="form.duration" class="form-control" placeholder="Duration (min)" type="number" /></div>
            <div class="col-md-4"><input v-model="form.max_marks" class="form-control" placeholder="Max Marks" type="number" /></div>
            <div class="col-md-6">
              <label class="form-label small">Slot Creation Start</label>
              <input v-model="form.slot_creation_start" class="form-control" type="datetime-local" />
            </div>
            <div class="col-md-6">
              <label class="form-label small">Slot Creation End</label>
              <input v-model="form.slot_creation_end" class="form-control" type="datetime-local" />
            </div>
            <div class="col-md-6">
              <label class="form-label small">Booking Start</label>
              <input v-model="form.booking_start" class="form-control" type="datetime-local" />
            </div>
            <div class="col-md-6">
              <label class="form-label small">Booking End</label>
              <input v-model="form.booking_end" class="form-control" type="datetime-local" />
            </div>
            <div class="col-md-6">
              <label class="form-label small">Status</label>
              <select v-model="form.status" class="form-select">
                <option>Draft</option><option>Slot Creation</option>
                <option>Booking Open</option><option>Closed</option><option>Completed</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="form.show=false">Cancel</button>
          <button class="btn btn-primary" @click="save">Save</button>
        </div>
      </div></div>
    </div>

    <!-- Rubric Modal -->
    <div v-if="rubricModal.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Rubrics — {{ rubricModal.examName }}</h5>
          <button class="btn-close" @click="rubricModal.show=false"></button>
        </div>
        <div class="modal-body">
          <table class="table table-sm mb-3">
            <thead><tr><th>Criterion</th><th>Max</th><th>Weight</th><th></th></tr></thead>
            <tbody>
              <tr v-for="r in rubricModal.rubrics" :key="r.id">
                <td>{{ r.criterion_name }}</td>
                <td>{{ r.max_marks }}</td>
                <td>{{ r.weightage }}</td>
                <td><button class="btn btn-sm btn-outline-danger" @click="deleteRubric(r.id)">×</button></td>
              </tr>
            </tbody>
          </table>
          <div class="row g-2">
            <div class="col-5"><input v-model="rubricForm.criterion_name" class="form-control" placeholder="Criterion" /></div>
            <div class="col-3"><input v-model.number="rubricForm.max_marks" class="form-control" placeholder="Max" type="number" /></div>
            <div class="col-2"><input v-model.number="rubricForm.weightage" class="form-control" placeholder="Wt" type="number" step="0.1" /></div>
            <div class="col-2"><button class="btn btn-primary w-100" @click="addRubric">Add</button></div>
          </div>
        </div>
      </div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const exams = ref([])
const courses = ref([])
const search = ref('')
const msg = ref('')
const formError = ref('')
const form = ref({ show: false, id: null, name: '', course_id: '', exam_type: '',
  duration: '', max_marks: '', slot_creation_start: '', slot_creation_end: '',
  booking_start: '', booking_end: '', status: 'Draft' })
const rubricModal = ref({ show: false, examId: null, examName: '', rubrics: [] })
const rubricForm = ref({ criterion_name: '', max_marks: '', weightage: 1 })

onMounted(async () => {
  await load()
  const cr = await api.getCourses()
  courses.value = cr.data
})

async function load() {
  const res = await api.getExaminations(search.value)
  exams.value = res.data
}

function openCreate() {
  Object.assign(form.value, { show: true, id: null, name: '', course_id: '', exam_type: '',
    duration: '', max_marks: '', slot_creation_start: '', slot_creation_end: '',
    booking_start: '', booking_end: '', status: 'Draft' })
  formError.value = ''
}

function edit(e) {
  Object.assign(form.value, { show: true, ...e,
    slot_creation_start: e.slot_creation_start ? e.slot_creation_start.slice(0,16) : '',
    slot_creation_end: e.slot_creation_end ? e.slot_creation_end.slice(0,16) : '',
    booking_start: e.booking_start ? e.booking_start.slice(0,16) : '',
    booking_end: e.booking_end ? e.booking_end.slice(0,16) : '',
  })
  formError.value = ''
}

async function save() {
  formError.value = ''
  try {
    if (form.value.id) await api.updateExamination(form.value.id, form.value)
    else await api.createExamination(form.value)
    form.value.show = false
    msg.value = 'Saved!'
    setTimeout(() => msg.value = '', 2000)
    await load()
  } catch (e) { formError.value = e.response?.data?.error || 'Error' }
}

async function remove(id) {
  if (!confirm('Delete?')) return
  await api.deleteExamination(id)
  await load()
}

async function publish(id) {
  if (!confirm('Publish results for this exam?')) return
  try {
    const res = await api.publishResults(id)
    msg.value = res.data.message
    setTimeout(() => msg.value = '', 3000)
    await load()
  } catch (e) { alert(e.response?.data?.error) }
}

async function manageRubrics(e) {
  rubricModal.value.show = true
  rubricModal.value.examId = e.id
  rubricModal.value.examName = e.name
  await loadRubrics()
}

async function loadRubrics() {
  const res = await api.getRubrics(rubricModal.value.examId)
  rubricModal.value.rubrics = res.data
}

async function addRubric() {
  await api.createRubric(rubricModal.value.examId, rubricForm.value)
  rubricForm.value = { criterion_name: '', max_marks: '', weightage: 1 }
  await loadRubrics()
}

async function deleteRubric(id) {
  await api.deleteRubric(id)
  await loadRubrics()
}

function statusClass(s) {
  return { 'bg-secondary': s==='Draft', 'bg-warning text-dark': s==='Slot Creation',
    'bg-primary': s==='Booking Open', 'bg-danger': s==='Closed', 'bg-success': s==='Completed' }
}
</script>
