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
  const hostname = window.location.hostname
  const mcpPort = parseInt(window.location.port || '9000') + 1
  return JSON.stringify({
    mcpServers: {
      gateway: { url: `http://${hostname}:${mcpPort}/mcp` }
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

function statusText(status: string) {
  if (status === 'running') return t('server.statusRunning')
  if (status === 'stopped') return t('server.statusStopped')
  return t('server.statusError')
}
</script>

<template>
  <div>
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="hero-inner">
        <h1 class="hero-title">{{ t('nav.title') }}</h1>
        <p class="hero-subtitle">{{ t('dashboard.heroDesc') }}</p>

        <div class="hero-stats">
          <div class="hero-stat-card">
            <div class="hero-stat-value">{{ store.systemInfo?.total_servers || 0 }}</div>
            <div class="hero-stat-label">{{ t('dashboard.totalServers') }}</div>
          </div>
          <div class="hero-stat-card">
            <div class="hero-stat-value">{{ store.systemInfo?.running || 0 }}</div>
            <div class="hero-stat-label">{{ t('dashboard.running') }}</div>
          </div>
          <div class="hero-stat-card">
            <div class="hero-stat-value">{{ store.systemInfo?.stopped || 0 }}</div>
            <div class="hero-stat-label">{{ t('dashboard.stopped') }}</div>
          </div>
          <div class="hero-stat-card">
            <div class="hero-stat-value">{{ store.systemInfo?.error || 0 }}</div>
            <div class="hero-stat-label">{{ t('dashboard.error') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Metric Cards (overlapping hero) -->
    <div class="page-container">
      <div class="metric-row">
        <div class="metric-card">
          <div class="metric-icon purple">
            <el-icon :size="22"><Operation /></el-icon>
          </div>
          <div>
            <div class="metric-value">{{ store.systemInfo?.total_tools || 0 }}</div>
            <div class="metric-label">{{ t('dashboard.totalTools') }}</div>
          </div>
        </div>
        <div class="metric-card">
          <div class="metric-icon green">
            <el-icon :size="22"><FolderOpened /></el-icon>
          </div>
          <div>
            <div class="metric-value">{{ store.systemInfo?.total_resources || 0 }}</div>
            <div class="metric-label">{{ t('dashboard.totalResources') }}</div>
          </div>
        </div>
        <div class="metric-card">
          <div class="metric-icon amber">
            <el-icon :size="22"><ChatDotRound /></el-icon>
          </div>
          <div>
            <div class="metric-value">{{ store.systemInfo?.total_prompts || 0 }}</div>
            <div class="metric-label">{{ t('dashboard.totalPrompts') }}</div>
          </div>
        </div>
      </div>

      <!-- Config & Server List -->
      <div class="grid-2" style="margin-top: 24px; padding-bottom: 40px">
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
              style="display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; border-bottom: 1px solid var(--border-light); cursor: pointer; transition: background 0.15s"
              @click="router.push(`/servers/${server.id}`)"
              @mouseenter="($event.currentTarget as HTMLElement).style.background = 'var(--border-light)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.background = ''"
            >
              <div style="display: flex; align-items: center; gap: 12px">
                <div class="server-card-icon" :class="server.project_type === 'python' ? 'python' : 'node'" style="width: 36px; height: 36px; font-size: 13px">
                  {{ server.project_type === 'python' ? 'Py' : 'JS' }}
                </div>
                <div>
                  <div style="font-weight: 500; font-size: 14px">{{ server.name }}</div>
                  <div style="font-size: 12px; color: var(--text-muted)">{{ server.tools_count }} tools</div>
                </div>
              </div>
              <span class="status-badge" :class="server.status">
                {{ statusText(server.status) }}
              </span>
            </div>
            <div v-if="!store.servers.length" class="empty-state" style="padding: 40px">
              <div style="color: var(--text-muted); font-size: 14px">{{ t('common.noData') }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
