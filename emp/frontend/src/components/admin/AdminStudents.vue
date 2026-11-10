<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <input v-model="search" class="form-control w-auto" placeholder="Search students…" @input="load" />
    </div>
    <table class="table table-bordered table-hover bg-white">
      <thead class="table-primary">
        <tr><th>#</th><th>Username</th><th>Email</th><th>Active</th></tr>
      </thead>
      <tbody>
        <tr v-for="s in students" :key="s.id">
          <td>{{ s.id }}</td>
          <td>{{ s.username }}</td>
          <td>{{ s.email }}</td>
          <td><span :class="s.active ? 'badge bg-success' : 'badge bg-danger'">{{ s.active ? 'Yes' : 'No' }}</span></td>
        </tr>
        <tr v-if="!students.length"><td colspan="4" class="text-center text-muted">No students</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const students = ref([])
const search = ref('')

onMounted(load)

async function load() {
  const res = await api.getStudents(search.value)
  students.value = res.data
}
</script>
