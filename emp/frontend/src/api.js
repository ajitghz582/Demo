import axios from 'axios'

export function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('token')}` }
}

export const api = {
  // Auth
  login: (data) => axios.post('/login', data),
  register: (data) => axios.post('/register', data),

  // Admin
  adminDashboard: () => axios.get('/api/admin/dashboard', { headers: authHeaders() }),
  getCourses: (q = '') => axios.get(`/api/admin/courses?q=${q}`, { headers: authHeaders() }),
  createCourse: (d) => axios.post('/api/admin/courses', d, { headers: authHeaders() }),
  updateCourse: (id, d) => axios.put(`/api/admin/courses/${id}`, d, { headers: authHeaders() }),
  deleteCourse: (id) => axios.delete(`/api/admin/courses/${id}`, { headers: authHeaders() }),

  getExaminations: (q = '') => axios.get(`/api/admin/examinations?q=${q}`, { headers: authHeaders() }),
  createExamination: (d) => axios.post('/api/admin/examinations', d, { headers: authHeaders() }),
  updateExamination: (id, d) => axios.put(`/api/admin/examinations/${id}`, d, { headers: authHeaders() }),
  deleteExamination: (id) => axios.delete(`/api/admin/examinations/${id}`, { headers: authHeaders() }),
  publishResults: (id) => axios.post(`/api/admin/examinations/${id}/publish`, {}, { headers: authHeaders() }),

  getRubrics: (examId) => axios.get(`/api/admin/examinations/${examId}/rubrics`, { headers: authHeaders() }),
  createRubric: (examId, d) => axios.post(`/api/admin/examinations/${examId}/rubrics`, d, { headers: authHeaders() }),
  deleteRubric: (id) => axios.delete(`/api/admin/rubrics/${id}`, { headers: authHeaders() }),

  getExaminers: (q = '') => axios.get(`/api/admin/examiners?q=${q}`, { headers: authHeaders() }),
  createExaminer: (d) => axios.post('/api/admin/examiners', d, { headers: authHeaders() }),
  updateExaminer: (id, d) => axios.put(`/api/admin/examiners/${id}`, d, { headers: authHeaders() }),
  deleteExaminer: (id) => axios.delete(`/api/admin/examiners/${id}`, { headers: authHeaders() }),

  getStudents: (q = '') => axios.get(`/api/admin/students?q=${q}`, { headers: authHeaders() }),
  getAdminSlots: (examId = '') => axios.get(`/api/admin/slots${examId ? '?exam_id=' + examId : ''}`, { headers: authHeaders() }),
  getAdminBookings: (q = '') => axios.get(`/api/admin/bookings?q=${q}`, { headers: authHeaders() }),
  rescheduleBooking: (id, data) => axios.put(`/api/admin/bookings/${id}/reschedule`, data, { headers: authHeaders() }),
  reassignExaminer: (id, data) => axios.put(`/api/admin/bookings/${id}/reassign`, data, { headers: authHeaders() }),

  // Examiner
  examinerDashboard: () => axios.get('/api/examiner/dashboard', { headers: authHeaders() }),
  examinerExams: () => axios.get('/api/examiner/examinations', { headers: authHeaders() }),
  examinerSlots: () => axios.get('/api/examiner/slots', { headers: authHeaders() }),
  createSlot: (d) => axios.post('/api/examiner/slots', d, { headers: authHeaders() }),
  updateSlot: (id, d) => axios.put(`/api/examiner/slots/${id}`, d, { headers: authHeaders() }),
  deleteSlot: (id) => axios.delete(`/api/examiner/slots/${id}`, { headers: authHeaders() }),
  slotStudents: (sid) => axios.get(`/api/examiner/slots/${sid}/students`, { headers: authHeaders() }),
  submitEvaluation: (bookingId, d) => axios.post(`/api/examiner/evaluate/${bookingId}`, d, { headers: authHeaders() }),

  // Student
  studentDashboard: () => axios.get('/api/student/dashboard', { headers: authHeaders() }),
  studentExams: (q = '', type = '') => axios.get(`/api/student/examinations?q=${q}&type=${type}`, { headers: authHeaders() }),
  studentSlots: (examId) => axios.get(`/api/student/slots/${examId}`, { headers: authHeaders() }),
  getMyBookings: () => axios.get('/api/student/bookings', { headers: authHeaders() }),
  bookSlot: (d) => axios.post('/api/student/bookings', d, { headers: authHeaders() }),
  cancelBooking: (id) => axios.delete(`/api/student/bookings/${id}`, { headers: authHeaders() }),
  getResults: () => axios.get('/api/student/results', { headers: authHeaders() }),
  getProfile: () => axios.get('/api/student/profile', { headers: authHeaders() }),
  updateProfile: (d) => axios.put('/api/student/profile', d, { headers: authHeaders() }),
  exportHistory: () => axios.get('/api/student/export', { headers: authHeaders() }),
}
