<script setup lang="ts">
import { onMounted } from 'vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMcpStore } from '../stores/mcp'
import { serverApi } from '../api/mcp'
import AddServerDialog from '../components/AddServerDialog.vue'

const { t } = useI18n()
const router = useRouter()
const store = useMcpStore()
const showAddDialog = ref(false)

onMounted(() => store.fetchServers())

async function handleStart(id: number) {
  await serverApi.start(id)
  ElMessage.success(t('server.started'))
  store.fetchServers()
}

async function handleStop(id: number) {
  await serverApi.stop(id)
  ElMessage.success(t('server.statusStopped'))
  store.fetchServers()
}

async function handleRestart(id: number) {
  await serverApi.restart(id)
  ElMessage.success(t('server.restarted'))
  store.fetchServers()
}

async function handleUpdate(id: number) {
  const res = await serverApi.updateRepo(id)
  ElMessage.success(res.message)
  store.fetchServers()
}

async function handleDelete(id: number, name: string) {
  try {
    await ElMessageBox.confirm(
      t('server.deleteConfirm', { name }),
      t('common.confirm'),
      { confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    await serverApi.delete(id, true)
    ElMessage.success(t('server.deleted'))
    store.fetchServers()
  } catch { /* cancelled */ }
}

function statusText(status: string) {
  if (status === 'running') return t('server.statusRunning')
  if (status === 'stopped') return t('server.statusStopped')
  return t('server.statusError')
}
</script>

<template>
  <div class="page-container" style="padding-top: 32px; padding-bottom: 40px">
    <!-- Section Header -->
    <div class="section-header">
      <div>
        <h2 class="section-title">{{ t('server.title') }}</h2>
        <p class="section-subtitle">{{ store.servers.length }} {{ t('dashboard.totalServers').toLowerCase() }}</p>
      </div>
      <el-button type="primary" round @click="showAddDialog = true">
        <el-icon style="margin-right: 6px"><Plus /></el-icon>
        {{ t('server.addServer') }}
      </el-button>
    </div>

    <!-- Server Cards Grid -->
    <div v-if="store.servers.length" class="server-grid" v-loading="store.loading">
      <div
        v-for="server in store.servers"
        :key="server.id"
        class="server-card"
        :class="server.status"
        @click="router.push(`/servers/${server.id}`)"
      >
        <div class="server-card-top">
          <div style="display: flex; align-items: center; gap: 12px">
            <div class="server-card-icon" :class="server.project_type === 'python' ? 'python' : 'node'">
              {{ server.project_type === 'python' ? 'Py' : 'JS' }}
            </div>
            <div>
              <div class="server-card-name">{{ server.name }}</div>
              <div class="server-card-url">{{ server.github_url || server.local_path }}</div>
            </div>
          </div>
          <span class="status-badge" :class="server.status">
            {{ statusText(server.status) }}
          </span>
        </div>

        <div class="server-card-meta">
          <div class="server-card-meta-item">
            <el-icon :size="14"><Operation /></el-icon>
            <span class="meta-value">{{ server.tools_count }}</span> tools
          </div>
          <div class="server-card-meta-item" v-if="server.last_commit">
            <el-icon :size="14"><DocumentCopy /></el-icon>
            <span class="meta-value" style="font-family: monospace">{{ server.last_commit?.slice(0, 7) }}</span>
          </div>
          <div class="server-card-meta-item" v-if="server.auto_update">
            <el-icon :size="14"><Refresh /></el-icon>
            {{ t('server.autoUpdate') }}
          </div>
        </div>

        <div class="server-card-actions" @click.stop>
          <el-button v-if="server.status !== 'running'" size="small" type="success" plain round @click="handleStart(server.id)">
            {{ t('server.start') }}
          </el-button>
          <el-button v-if="server.status === 'running'" size="small" type="warning" plain round @click="handleStop(server.id)">
            {{ t('server.stop') }}
          </el-button>
          <el-button v-if="server.status === 'running'" size="small" plain round @click="handleRestart(server.id)">
            {{ t('server.restart') }}
          </el-button>
          <el-button v-if="server.github_url" size="small" type="info" plain round @click="handleUpdate(server.id)">
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-button size="small" type="danger" plain round @click="handleDelete(server.id, server.name)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!store.loading" class="card">
      <div class="empty-state">
        <div class="empty-state-icon">
          <el-icon :size="28"><Monitor /></el-icon>
        </div>
        <div class="empty-state-text">{{ t('common.noData') }}</div>
        <el-button type="primary" round style="margin-top: 16px" @click="showAddDialog = true">
          <el-icon style="margin-right: 6px"><Plus /></el-icon>
          {{ t('server.addServer') }}
        </el-button>
      </div>
    </div>

    <AddServerDialog v-model="showAddDialog" @added="() => { showAddDialog = false; store.fetchServers() }" />
  </div>
</template>
