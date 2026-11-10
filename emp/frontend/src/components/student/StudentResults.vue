<template>
  <div>
    <h5 class="mb-3">Published Results</h5>
    <div v-if="!results.length" class="text-muted">No results published yet.</div>
    <div class="row g-3">
      <div class="col-md-6" v-for="r in results" :key="r.evaluation_id">
        <div class="card shadow-sm">
          <div class="card-body">
            <h6 class="card-title">{{ r.exam_name }}</h6>
            <p class="card-text small text-muted mb-1">{{ r.course }}</p>
            <div class="d-flex gap-3 mb-2">
              <span class="fw-bold fs-4 text-success">{{ r.total_marks }}</span>
              <span class="text-muted align-self-end">/ {{ r.max_marks }}</span>
            </div>
            <p class="small"><strong>Examiner:</strong> {{ r.examiner }}</p>
            <p class="small"><strong>Remarks:</strong> {{ r.remarks || '—' }}</p>
            <p class="small text-muted">Evaluated: {{ r.eval_date?.slice(0,10) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const results = ref([])
onMounted(async () => {
  const res = await api.getResults()
  results.value = res.data
})
</script>
