<template>
  <div style="max-width:400px">
    <h5 class="mb-3">My Profile</h5>
    <div v-if="msg" class="alert py-2" :class="msgType==='success'?'alert-success':'alert-danger'">{{ msg }}</div>
    <div class="mb-2">
      <label class="form-label small">Username</label>
      <input :value="profile.username" class="form-control" disabled />
    </div>
    <div class="mb-2">
      <label class="form-label small">Email</label>
      <input v-model="form.email" class="form-control" />
    </div>
    <div class="mb-3">
      <label class="form-label small">New Password (leave blank to keep)</label>
      <input v-model="form.password" type="password" class="form-control" />
    </div>
    <button class="btn btn-primary" @click="save">Update Profile</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../api.js'

const profile = ref({})
const form = ref({ email: '', password: '' })
const msg = ref('')
const msgType = ref('success')

onMounted(async () => {
  const res = await api.getProfile()
  profile.value = res.data
  form.value.email = res.data.email
})

async function save() {
  try {
    await api.updateProfile({ email: form.value.email, password: form.value.password })
    msg.value = 'Profile updated!'
    msgType.value = 'success'
    form.value.password = ''
  } catch (e) {
    msg.value = e.response?.data?.error || 'Error'
    msgType.value = 'danger'
  }
  setTimeout(() => msg.value = '', 3000)
}
</script>
