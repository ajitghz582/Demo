<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <input v-model="search" class="form-control w-auto" placeholder="Search courses…" @input="load" />
      <button class="btn btn-primary" @click="openCreate">+ New Course</button>
    </div>

    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-primary">
        <tr><th>Code</th><th>Name</th><th>Description</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="c in courses" :key="c.id">
          <td>{{ c.course_code }}</td>
          <td>{{ c.course_name }}</td>
          <td>{{ c.description }}</td>
          <td><span :class="c.status === 'active' ? 'badge bg-success' : 'badge bg-secondary'">{{ c.status }}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-primary me-1" @click="edit(c)">Edit</button>
            <button class="btn btn-sm btn-outline-danger" @click="remove(c.id)">Delete</button>
          </td>
        </tr>
        <tr v-if="!courses.length"><td colspan="5" class="text-center text-muted">No courses found</td></tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div v-if="form.show" class="modal d-block" style="background:rgba(0,0,0,.4)">
      <div class="modal-dialog"><div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">{{ form.id ? 'Edit' : 'New' }} Course</h5>
          <button class="btn-close" @click="form.show=false"></button>
        </div>
        <div class="modal-body">
          <div v-if="formError" class="alert alert-danger py-2">{{ formError }}</div>
          <input v-model="form.course_code" class="form-control mb-2" placeholder="Course Code" />
          <input v-model="form.course_name" class="form-control mb-2" placeholder="Course Name" />
          <textarea v-model="form.description" class="form-control mb-2" placeholder="Description" rows="2"></textarea>
          <select v-if="form.id" v-model="form.status" class="form-select">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
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

const courses = ref([])
const search = ref('')
const msg = ref('')
const formError = ref('')
const form = ref({ show: false, id: null, course_code: '', course_name: '', description: '', status: 'active' })

onMounted(load)

async function load() {
  try {
    const res = await api.getCourses(search.value)
    courses.value = res.data
  } catch {}
}

function openCreate() {
  Object.assign(form.value, { show: true, id: null, course_code: '', course_name: '', description: '', status: 'active' })
  formError.value = ''
}

function edit(c) {
  Object.assign(form.value, { show: true, ...c })
  formError.value = ''
}

async function save() {
  formError.value = ''
  try {
    if (form.value.id) {
      await api.updateCourse(form.value.id, form.value)
    } else {
      await api.createCourse(form.value)
    }
    form.value.show = false
    msg.value = 'Saved!'
    setTimeout(() => msg.value = '', 2000)
    await load()
  } catch (e) {
    formError.value = e.response?.data?.error || 'Error saving course'
  }
}

async function remove(id) {
  if (!confirm('Delete this course?')) return
  try {
    await api.deleteCourse(id)
    await load()
  } catch (e) {
    alert(e.response?.data?.error || 'Delete failed')
  }
}
</script>
