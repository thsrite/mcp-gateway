<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMcpStore } from '../stores/mcp'
import { ElMessage } from 'element-plus'

const { t } = useI18n()
const router = useRouter()
const store = useMcpStore()
const copied = ref(false)

onMounted(async () => {
  await store.fetchSystemInfo()
  await store.fetchServers()
})

const configJson = computed(() => {
  const origin = window.location.origin
  return JSON.stringify({
    mcpServers: {
      gateway: { url: `${origin}/mcp` }
    }
  }, null, 2)
})

async function copyConfig() {
  try {
    await navigator.clipboard.writeText(configJson.value)
    copied.value = true
    ElMessage.success(t('dashboard.copied'))
    setTimeout(() => copied.value = false, 2000)
  } catch {
    ElMessage.error('Copy failed')
  }
}
</script>

<template>
  <div>
    <!-- Stat Cards -->
    <div class="grid-4" style="margin-bottom: 24px">
      <div class="stat-card">
        <div class="stat-icon primary">
          <el-icon :size="24"><Monitor /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ store.systemInfo?.total_servers || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.totalServers') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <el-icon :size="24"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value" style="color: var(--success)">{{ store.systemInfo?.running || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.running') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning">
          <el-icon :size="24"><Remove /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value" style="color: var(--warning)">{{ store.systemInfo?.stopped || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.stopped') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon danger">
          <el-icon :size="24"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value" style="color: var(--danger)">{{ store.systemInfo?.error || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.error') }}</div>
        </div>
      </div>
    </div>

    <!-- Tools / Resources / Prompts -->
    <div class="grid-3" style="margin-bottom: 24px">
      <div class="stat-card">
        <div class="stat-icon primary">
          <el-icon :size="22"><Operation /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ store.systemInfo?.total_tools || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.totalTools') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <el-icon :size="22"><FolderOpened /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ store.systemInfo?.total_resources || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.totalResources') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning">
          <el-icon :size="22"><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ store.systemInfo?.total_prompts || 0 }}</div>
          <div class="stat-label">{{ t('dashboard.totalPrompts') }}</div>
        </div>
      </div>
    </div>

    <div class="grid-2">
      <!-- Gateway Config -->
      <div class="card">
        <div class="card-header">
          <h3>{{ t('dashboard.quickConfig') }}</h3>
          <el-tag size="small" effect="dark" round style="background: var(--primary); border: none">
            Streamable HTTP
          </el-tag>
        </div>
        <div class="card-body">
          <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 12px">
            {{ t('dashboard.configTip') }}
          </p>
          <div class="config-block">
            <pre>{{ configJson }}</pre>
            <el-button
              class="copy-btn"
              size="small"
              :type="copied ? 'success' : 'default'"
              @click="copyConfig"
            >
              <el-icon><DocumentCopy /></el-icon>
              {{ copied ? t('dashboard.copied') : t('dashboard.copyConfig') }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Server List Preview -->
      <div class="card">
        <div class="card-header">
          <h3>{{ t('dashboard.recentServers') }}</h3>
          <el-button link type="primary" @click="router.push('/servers')">
            {{ t('dashboard.viewAll') }}
            <el-icon style="margin-left: 4px"><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div class="card-body" style="padding: 0">
          <div
            v-for="server in store.servers.slice(0, 5)"
            :key="server.id"
            style="display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; border-bottom: 1px solid var(--border); cursor: pointer"
            @click="router.push(`/servers/${server.id}`)"
          >
            <div style="display: flex; align-items: center; gap: 12px">
              <div style="width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px"
                :style="{ background: server.project_type === 'python' ? '#EEF2FF' : '#FFF7ED', color: server.project_type === 'python' ? '#4F6EF7' : '#F59E0B' }"
              >
                {{ server.project_type === 'python' ? 'Py' : 'JS' }}
              </div>
              <div>
                <div style="font-weight: 500; font-size: 14px">{{ server.name }}</div>
                <div style="font-size: 12px; color: var(--text-muted)">
                  {{ server.tools_count }} tools
                </div>
              </div>
            </div>
            <span class="status-badge" :class="server.status">
              {{ server.status === 'running' ? t('server.statusRunning') : server.status === 'stopped' ? t('server.statusStopped') : t('server.statusError') }}
            </span>
          </div>
          <div v-if="!store.servers.length" style="padding: 40px; text-align: center; color: var(--text-muted)">
            {{ t('common.noData') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
