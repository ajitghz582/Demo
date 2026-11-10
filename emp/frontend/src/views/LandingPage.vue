<template>
  <div class="min-vh-100 d-flex align-items-center justify-content-center bg-light">
    <div class="card shadow p-4" style="min-width:360px">
      <h2 class="text-center mb-1 fw-bold text-primary">EMP</h2>
      <p class="text-center text-muted mb-4">Examination Management Portal</p>

      <div v-if="!showRegister">
        <h5 class="mb-3">Login</h5>
        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
        <input v-model="username" class="form-control mb-2" placeholder="Username" />
        <input v-model="password" type="password" class="form-control mb-3" placeholder="Password" />
        <button class="btn btn-primary w-100 mb-2" @click="login" :disabled="loading">
          {{ loading ? 'Logging in…' : 'Login' }}
        </button>
        <p class="text-center small mb-0">
          New student?
          <a href="#" @click.prevent="showRegister = true">Register here</a>
        </p>
      </div>

      <div v-else>
        <h5 class="mb-3">Student Registration</h5>
        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
        <div v-if="success" class="alert alert-success py-2">{{ success }}</div>
        <input v-model="username" class="form-control mb-2" placeholder="Username" />
        <input v-model="email" class="form-control mb-2" placeholder="Email" />
        <input v-model="password" type="password" class="form-control mb-3" placeholder="Password" />
        <button class="btn btn-success w-100 mb-2" @click="register" :disabled="loading">
          {{ loading ? 'Registering…' : 'Register' }}
        </button>
        <p class="text-center small mb-0">
          Already have an account?
          <a href="#" @click.prevent="showRegister = false">Login</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api.js'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const showRegister = ref(false)
const error = ref('')
const success = ref('')
const loading = ref(false)

async function login() {
  error.value = ''
  loading.value = true
  try {
    const res = await api.login({ username: username.value, password: password.value })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('role', res.data.role)
    localStorage.setItem('username', res.data.username)
    router.push('/' + res.data.role)
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}

async function register() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await api.register({ username: username.value, email: email.value, password: password.value })
    success.value = 'Registered! You can now log in.'
    showRegister.value = false
    password.value = ''
  } catch (e) {
    error.value = e.response?.data?.error || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
