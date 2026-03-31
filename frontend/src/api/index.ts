import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code !== 0) {
      ElMessage.error(data.message || 'Request failed')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    const msg = error.response?.data?.detail || error.message || 'Network error'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default api
