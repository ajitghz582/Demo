<template>
  <div>
    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <table class="table table-bordered table-hover bg-white">
      <thead class="table-success">
        <tr>
          <th>Exam Name</th>
          <th>Course</th>
          <th>Type</th>
          <th>Duration</th>
          <th>Max Marks</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="e in exams" :key="e.id">
          <td>{{ e.name }}</td>
          <td>{{ e.course_name }}</td>
          <td>{{ e.exam_type }}</td>
          <td>{{ e.duration }} min</td>
          <td>{{ e.max_marks }}</td>
          <td><span class="badge" :class="statusClass(e.status)">{{ e.status }}</span></td>
          <td>
            <button
              class="btn btn-sm btn-success"
              :disabled="e.status !== 'Slot Creation'"
              @click="$emit('create-slot', e)"
              :title="e.status !== 'Slot Creation' ? 'Slot creation not open for this exam' : 'Create a slot'"
            >
              + Add Slot
            </button>
          </td>
        </tr>
        <tr v-if="!exams.length">
          <td colspan="7" class="text-center text-muted">No examinations assigned yet</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

defineEmits(['create-slot'])

const exams = ref([])
const msg = ref('')

onMounted(async () => {
  try {
    const res = await api.examinerExams()
    exams.value = res.data
  } catch {
    msg.value = 'Failed to load assigned examinations.'
  }
})

function statusClass(s) {
  return {
    'bg-secondary': s === 'Draft',
    'bg-warning text-dark': s === 'Slot Creation',
    'bg-primary': s === 'Booking Open',
    'bg-danger': s === 'Closed',
    'bg-success': s === 'Completed',
  }
}
</script>
