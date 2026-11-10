<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <input v-model="search" class="form-control w-auto" placeholder="Search examiners…" @input="load" />
      <button class="btn btn-primary" @click="openCreate">+ Add Examiner</button>
    </div>
    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-primary">
        <tr><th>Username</th><th>Email</th><th>Department</th><th>Contact</th><th>Active</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="e in examiners" :key="e.id">
          <td>{{ e.username }}</td>
          <td>{{ e.email }}</td>
          <td>{{ e.department }}</td>
          <td>{{ e.contact }}</td>
          <td><span :class="e.active ? 'badge bg-success' : 'badge bg-danger'">{{ e.active ? 'Yes' : 'No' }}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-primary me-1" @click="edit(e)">Edit</button>
            <button class="btn btn-sm btn-outline-danger" @click="deactivate(e.id)">Deactivate</button>
          </td>
        </tr>
        <tr v-if="!examiners.length"><td colspan="6" class="text-center text-muted">No examiners</td></tr>
      </tbody>
    </table>

    <div v-if="form.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ form.id ? 'Edit' : 'Add' }} Examiner</h5>
          <button class="btn-close" @click="form.show=false"></button>
        </div>
        <div class="modal-body">
          <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
          <input v-if="!form.id" v-model="form.username" class="form-control mb-2" placeholder="Username" />
          <input v-model="form.email" class="form-control mb-2" placeholder="Email" />
          <input v-if="!form.id" v-model="form.password" type="password" class="form-control mb-2" placeholder="Password" />
          <input v-model="form.department" class="form-control mb-2" placeholder="Department" />
          <input v-model="form.contact" class="form-control mb-2" placeholder="Contact" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="form.show=false">Cancel</button>
          <button class="btn btn-primary" @click="save">Save</button>
        </div>
      </div></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const examiners = ref([])
const search = ref('')
const msg = ref('')
const formError = ref('')
const form = ref({ show: false, id: null, username: '', email: '', password: '', department: '', contact: '' })

onMounted(load)

async function load() {
  const res = await api.getExaminers(search.value)
  examiners.value = res.data
}

function openCreate() {
  Object.assign(form.value, { show: true, id: null, username: '', email: '', password: '', department: '', contact: '' })
  formError.value = ''
}

function edit(e) {
  Object.assign(form.value, { show: true, ...e })
  formError.value = ''
}

async function save() {
  formError.value = ''
  try {
    if (form.value.id) await api.updateExaminer(form.value.id, form.value)
    else await api.createExaminer(form.value)
    form.value.show = false
    msg.value = 'Saved!'
    setTimeout(() => msg.value = '', 2000)
    await load()
  } catch (e) { formError.value = e.response?.data?.error || 'Error' }
}

async function deactivate(id) {
  if (!confirm('Deactivate this examiner?')) return
  await api.deleteExaminer(id)
  await load()
}
</script>
