import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
});

export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common['Authorization'];
  }
}

// If a request comes back 401 (expired/invalid token), force a clean
// logout instead of leaving the app stuck on a broken authenticated
// state — the login page is the only sane recovery point.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('gradeai_auth');
      setAuthToken(null);
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Health
  checkHealth: async () => {
    const { data } = await client.get('/health');
    return data;
  },

  // Auth
  login: async (username, password) => {
    const { data } = await client.post('/auth/login', { username, password });
    return data;
  },

  getMe: async () => {
    const { data } = await client.get('/auth/me');
    return data;
  },

  changePassword: async (old_password, new_password) => {
    const { data } = await client.post('/auth/change-password', { old_password, new_password });
    return data;
  },

  // Admin — user management
  createUser: async (payload) => {
    const { data } = await client.post('/admin/users', payload);
    return data;
  },

  listUsers: async (role = '') => {
    const { data } = await client.get('/admin/users', { params: role ? { role } : {} });
    return data;
  },

  deleteUser: async (userId) => {
    const { data } = await client.delete(`/admin/users/${userId}`);
    return data;
  },

  // Dashboard Stats
  getDashboardStats: async () => {
    const { data } = await client.get('/exams/dashboard/stats');
    return data;
  },

  // Exams (containers)
  getExams: async () => {
    const { data } = await client.get('/exams');
    return data;
  },

  getExam: async (examId) => {
    const { data } = await client.get(`/exams/${examId}`);
    return data;
  },

  createExam: async ({ title, term }) => {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('term', term || '');
    const { data } = await client.post('/exams', formData);
    return data;
  },

  deleteExam: async (examId) => {
    const { data } = await client.delete(`/exams/${examId}`);
    return data;
  },

  // Subject-papers (one subject under an exam)
  listSubjectPapers: async (examId) => {
    const { data } = await client.get(`/exams/${examId}/subjects`);
    return data;
  },

  createSubjectPaper: async (examId, { subject_name, subject_code, question_paper, answer_key }) => {
    const formData = new FormData();
    formData.append('subject_name', subject_name);
    formData.append('subject_code', subject_code);
    formData.append('question_paper', question_paper);
    formData.append('answer_key', answer_key);
    const { data } = await client.post(`/exams/${examId}/subjects`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  getSubjectPaper: async (subjectPaperId) => {
    const { data } = await client.get(`/subjects/${subjectPaperId}`);
    return data;
  },

  listSubmissions: async (subjectPaperId) => {
    const { data } = await client.get(`/subjects/${subjectPaperId}/submissions`);
    return data;
  },

  // Submissions
  uploadSubmission: async (subjectPaperId, { roll_no, student_name, student_answer }) => {
    const formData = new FormData();
    formData.append('roll_no', roll_no);
    formData.append('student_name', student_name);
    formData.append('student_answer', student_answer);
    const { data } = await client.post(`/subjects/${subjectPaperId}/submissions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  // Grading
  triggerGrading: async (submissionId) => {
    const { data } = await client.post(`/grade/${submissionId}`);
    return data;
  },

  getGradingStatus: async (submissionId) => {
    const { data } = await client.get(`/results/submission/${submissionId}/status`);
    return data;
  },

  // Results
  getResult: async (submissionId) => {
    const { data } = await client.get(`/results/${submissionId}`);
    return data;
  },

  getSubjectResults: async (subjectPaperId) => {
    const { data } = await client.get(`/results/subject/${subjectPaperId}`);
    return data;
  },

  getMyResults: async () => {
    const { data } = await client.get('/results/student/me');
    return data;
  },

  // Analytics
  getSubjectAnalytics: async (examId, subjectCode) => {
    const { data } = await client.get(`/analytics/${examId}/${subjectCode}`);
    return data;
  },
};

export default client;
