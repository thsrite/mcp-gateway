<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { authApi, systemApi } from '../api/mcp'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const settings = ref({
  update_interval: 30,
  health_check_interval: 60,
  max_log_lines: 1000,
})
const saving = ref(false)

onMounted(async () => {
  try {
    const res = await systemApi.getSettings()
    settings.value.update_interval = res.data.update_interval_minutes
    settings.value.health_check_interval = res.data.health_check_interval_seconds
    settings.value.max_log_lines = res.data.max_log_lines
  } catch { /* use defaults */ }
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const changingPassword = ref(false)
const toggling = ref(false)
const regenerating = ref(false)
const apiKeyCopied = ref(false)

const showSetup = ref(false)
const setupForm = ref({ username: '', password: '', confirmPassword: '' })
const settingUp = ref(false)

async function handleSave() {
  saving.value = true
  try {
    await systemApi.updateSettings({
      update_interval_minutes: settings.value.update_interval,
      health_check_interval_seconds: settings.value.health_check_interval,
      max_log_lines: settings.value.max_log_lines,
    })
    ElMessage.success(t('settings.saved'))
  } catch { /* interceptor handles */ } finally {
    saving.value = false
  }
}

async function handleToggleAuth(enabled: boolean) {
  if (enabled && !auth.initialized) {
    showSetup.value = true
    auth.authEnabled = false
    return
  }

  if (!enabled) {
    try {
      await ElMessageBox.confirm(
        t('settings.authDisableConfirm'),
        t('common.confirm'),
        { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
      )
    } catch {
      auth.authEnabled = true
      return
    }
  }

  toggling.value = true
  try {
    const res = await authApi.toggle(enabled)
    auth.authEnabled = enabled
    if (res.data.api_key) auth.apiKey = res.data.api_key
    ElMessage.success(enabled ? t('settings.authEnabled') : t('settings.authDisabled'))
    if (enabled && !auth.token) {
      router.push('/login')
    }
  } catch {
    auth.authEnabled = !enabled
  } finally {
    toggling.value = false
  }
}

async function handleSetupAndEnable() {
  if (!setupForm.value.username || !setupForm.value.password) {
    ElMessage.warning(t('common.required'))
    return
  }
  if (setupForm.value.password !== setupForm.value.confirmPassword) {
    ElMessage.warning(t('auth.passwordMismatch'))
    return
  }

  settingUp.value = true
  try {
    const res = await authApi.setup(setupForm.value.username, setupForm.value.password)
    auth.setAuth(res.data.token, res.data.username)
    auth.initialized = true
    const toggleRes = await authApi.toggle(true)
    auth.authEnabled = true
    if (toggleRes.data.api_key) auth.apiKey = toggleRes.data.api_key
    showSetup.value = false
    ElMessage.success(t('auth.setupSuccess'))
  } catch { /* interceptor handles */ } finally {
    settingUp.value = false
  }
}

async function copyApiKey() {
  try {
    await navigator.clipboard.writeText(auth.apiKey)
    apiKeyCopied.value = true
    ElMessage.success(t('dashboard.copied'))
    setTimeout(() => apiKeyCopied.value = false, 2000)
  } catch {
    ElMessage.error('Copy failed')
  }
}

async function regenerateApiKey() {
  regenerating.value = true
  try {
    const res = await authApi.regenerateKey()
    auth.apiKey = res.data.api_key
    ElMessage.success(t('settings.apiKeyRegenerated'))
  } catch { /* interceptor handles */ } finally {
    regenerating.value = false
  }
}

async function handleChangePassword() {
  if (!passwordForm.value.old_password || !passwordForm.value.new_password) {
    ElMessage.warning(t('common.required'))
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning(t('auth.passwordMismatch'))
    return
  }
  changingPassword.value = true
  try {
    await authApi.changePassword(passwordForm.value.old_password, passwordForm.value.new_password)
    ElMessage.success(t('auth.passwordChanged'))
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch { /* interceptor handles */ } finally {
    changingPassword.value = false
  }
}
</script>

<template>
  <div class="page-container" style="padding-top: 32px; padding-bottom: 40px">
    <div class="section-header" style="margin-bottom: 24px">
      <div>
        <h2 class="section-title">{{ t('settings.title') }}</h2>
      </div>
    </div>

    <!-- Two-column layout -->
    <div class="settings-grid">
      <!-- Left: General Settings -->
      <div class="card">
        <div class="card-header">
          <h3>{{ t('settings.general') }}</h3>
        </div>
        <div class="card-body">
          <el-form label-position="top">
            <el-form-item :label="t('settings.gitPullInterval')">
              <el-input-number v-model="settings.update_interval" :min="1" :max="1440" size="large" style="width: 100%" />
            </el-form-item>
            <el-form-item :label="t('settings.healthCheckInterval')">
              <el-input-number v-model="settings.health_check_interval" :min="10" :max="3600" size="large" style="width: 100%" />
            </el-form-item>
            <el-form-item :label="t('settings.maxLogLines')">
              <el-input-number v-model="settings.max_log_lines" :min="100" :max="10000" :step="100" size="large" style="width: 100%" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" round :loading="saving" @click="handleSave">{{ t('common.save') }}</el-button>
            </el-form-item>
          </el-form>

          <el-alert type="info" :closable="false" style="border-radius: var(--radius-sm)">
            <template #title>
              <span style="font-weight: 500">{{ t('settings.configFileTip') }}</span>
            </template>
            <span>{{ t('settings.saveHint') }}</span>
          </el-alert>
        </div>
      </div>

      <!-- Right: Auth Settings -->
      <div class="card">
        <div class="card-header">
          <h3>{{ t('settings.authTitle') }}</h3>
          <el-switch
            :model-value="auth.authEnabled"
            :loading="toggling"
            :active-text="t('settings.authEnabled')"
            :inactive-text="t('settings.authDisabled')"
            @change="handleToggleAuth"
          />
        </div>
        <div class="card-body">
          <!-- Setup form -->
          <template v-if="showSetup">
            <el-alert type="info" :closable="false" style="border-radius: var(--radius-sm); margin-bottom: 20px">
              <template #title>
                <span style="font-weight: 500">{{ t('auth.setupDesc') }}</span>
              </template>
            </el-alert>
            <el-form label-position="top">
              <el-form-item :label="t('auth.username')">
                <el-input v-model="setupForm.username" :placeholder="t('auth.usernamePlaceholder')" size="large" />
              </el-form-item>
              <div style="display: flex; gap: 12px">
                <el-form-item :label="t('auth.password')" style="flex: 1">
                  <el-input v-model="setupForm.password" type="password" :placeholder="t('auth.passwordPlaceholder')" size="large" show-password />
                </el-form-item>
                <el-form-item :label="t('auth.confirmPassword')" style="flex: 1">
                  <el-input v-model="setupForm.confirmPassword" type="password" :placeholder="t('auth.confirmPasswordPlaceholder')" size="large" show-password />
                </el-form-item>
              </div>
              <div style="display: flex; gap: 8px">
                <el-button type="primary" round :loading="settingUp" @click="handleSetupAndEnable">
                  {{ t('auth.createAndEnable') }}
                </el-button>
                <el-button round @click="showSetup = false">{{ t('common.cancel') }}</el-button>
              </div>
            </el-form>
          </template>

          <!-- Auth enabled -->
          <template v-else-if="auth.authEnabled">
            <el-alert type="success" :closable="false" style="border-radius: var(--radius-sm); margin-bottom: 20px">
              <template #title>
                <span style="font-weight: 500">{{ t('settings.authEnabledTip') }}</span>
              </template>
            </el-alert>

            <!-- MCP API Key -->
            <div v-if="auth.apiKey" style="margin-bottom: 24px">
              <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--text-primary)">
                MCP API Key
              </h4>
              <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px">
                {{ t('settings.apiKeyTip') }}
              </p>
              <div class="config-block" style="display: flex; align-items: center; gap: 12px; padding: 14px 16px">
                <code style="flex: 1; word-break: break-all; font-size: 13px">{{ auth.apiKey }}</code>
                <el-button size="small" :type="apiKeyCopied ? 'success' : 'default'" @click="copyApiKey">
                  <el-icon><DocumentCopy /></el-icon>
                </el-button>
                <el-button size="small" :loading="regenerating" @click="regenerateApiKey">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </div>

            <!-- Change Password -->
            <template v-if="auth.token">
              <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 16px; color: var(--text-primary)">
                {{ t('auth.changePassword') }}
              </h4>
              <el-form label-position="top">
                <el-form-item :label="t('auth.oldPassword')">
                  <el-input v-model="passwordForm.old_password" type="password" size="large" show-password />
                </el-form-item>
                <div style="display: flex; gap: 12px">
                  <el-form-item :label="t('auth.newPassword')" style="flex: 1">
                    <el-input v-model="passwordForm.new_password" type="password" size="large" show-password />
                  </el-form-item>
                  <el-form-item :label="t('auth.confirmPassword')" style="flex: 1">
                    <el-input v-model="passwordForm.confirm_password" type="password" size="large" show-password />
                  </el-form-item>
                </div>
                <el-button type="primary" round :loading="changingPassword" @click="handleChangePassword">
                  {{ t('auth.changePassword') }}
                </el-button>
              </el-form>
            </template>
          </template>

          <!-- Auth disabled -->
          <template v-else>
            <el-alert type="warning" :closable="false" style="border-radius: var(--radius-sm)">
              <template #title>
                <span style="font-weight: 500">{{ t('settings.authDisabledTip') }}</span>
              </template>
            </el-alert>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
