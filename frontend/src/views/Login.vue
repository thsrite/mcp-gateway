<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/mcp'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const isSetup = ref(false)
const loading = ref(false)
const form = ref({ username: '', password: '', confirmPassword: '' })

onMounted(async () => {
  await auth.fetchAuthStatus()
  if (!auth.authEnabled) {
    router.replace('/')
    return
  }
  isSetup.value = !auth.initialized
})

async function handleSubmit() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning(t('common.required'))
    return
  }

  if (isSetup.value && form.value.password !== form.value.confirmPassword) {
    ElMessage.warning(t('auth.passwordMismatch'))
    return
  }

  loading.value = true
  try {
    let res
    if (isSetup.value) {
      res = await authApi.setup(form.value.username, form.value.password)
    } else {
      res = await authApi.login(form.value.username, form.value.password)
    }
    auth.setAuth(res.data.token, res.data.username)
    ElMessage.success(isSetup.value ? t('auth.setupSuccess') : t('auth.loginSuccess'))
    router.replace('/')
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">G</div>
        <h1>{{ t('nav.title') }}</h1>
        <p>{{ isSetup ? t('auth.setupDesc') : t('auth.loginDesc') }}</p>
      </div>

      <el-form @submit.prevent="handleSubmit" label-position="top">
        <el-form-item :label="t('auth.username')">
          <el-input
            v-model="form.username"
            :placeholder="t('auth.usernamePlaceholder')"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item :label="t('auth.password')">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="t('auth.passwordPlaceholder')"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item v-if="isSetup" :label="t('auth.confirmPassword')">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            :placeholder="t('auth.confirmPasswordPlaceholder')"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          round
          style="width: 100%; margin-top: 8px"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ isSetup ? t('auth.createAdmin') : t('auth.login') }}
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-hero);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255,255,255,0.06) 0%, transparent 40%);
}

.login-card {
  position: relative;
  background: #fff;
  border-radius: 20px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 56px;
  height: 56px;
  background: var(--gradient-hero);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 22px;
  margin: 0 auto 16px;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.login-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.login-header p {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>
