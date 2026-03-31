<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

const { t } = useI18n()

const settings = ref({
  update_interval: 30,
  health_check_interval: 60,
  max_log_lines: 1000,
})

function handleSave() {
  ElMessage.info(t('settings.configFileTip'))
}
</script>

<template>
  <div>
    <div class="card" style="max-width: 640px">
      <div class="card-header">
        <h3>{{ t('settings.title') }}</h3>
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
            <el-button type="primary" round @click="handleSave">{{ t('common.save') }}</el-button>
          </el-form-item>
        </el-form>

        <el-alert
          type="info"
          :closable="false"
          style="margin-top: 16px; border-radius: var(--radius-sm)"
        >
          <template #title>
            <span style="font-weight: 500">{{ t('settings.configFileTip') }}</span>
          </template>
          <span>{{ t('settings.saveHint') }}</span>
        </el-alert>
      </div>
    </div>
  </div>
</template>
