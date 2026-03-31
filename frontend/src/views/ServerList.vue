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
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <div>
        <h3 style="font-size: 16px; font-weight: 600">{{ t('server.title') }}</h3>
        <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px">
          {{ store.servers.length }} {{ t('dashboard.totalServers').toLowerCase() }}
        </p>
      </div>
      <el-button type="primary" round @click="showAddDialog = true">
        <el-icon style="margin-right: 6px"><Plus /></el-icon>
        {{ t('server.addServer') }}
      </el-button>
    </div>

    <div class="card">
      <div class="card-body" style="padding: 0">
        <el-table :data="store.servers" v-loading="store.loading" style="width: 100%"
          :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: 600, fontSize: '13px' }"
          :row-style="{ cursor: 'pointer' }"
          @row-click="(row: any) => router.push(`/servers/${row.id}`)"
        >
          <el-table-column :label="t('common.name')" min-width="180">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; gap: 10px">
                <div style="width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; flex-shrink: 0"
                  :style="{
                    background: row.project_type === 'python' ? '#EEF2FF' : '#FFF7ED',
                    color: row.project_type === 'python' ? '#4F6EF7' : '#EA580C'
                  }"
                >
                  {{ row.project_type === 'python' ? 'Py' : 'JS' }}
                </div>
                <div>
                  <div style="font-weight: 500; color: var(--text-primary)">{{ row.name }}</div>
                  <div style="font-size: 12px; color: var(--text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
                    {{ row.github_url || row.local_path }}
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="t('common.status')" width="110">
            <template #default="{ row }">
              <span class="status-badge" :class="row.status">
                {{ row.status === 'running' ? t('server.statusRunning') : row.status === 'stopped' ? t('server.statusStopped') : t('server.statusError') }}
              </span>
            </template>
          </el-table-column>
          <el-table-column :label="t('server.toolsCount')" width="80" align="center">
            <template #default="{ row }">
              <span style="font-weight: 600; color: var(--primary)">{{ row.tools_count }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('server.commit')" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.last_commit" size="small" effect="plain" style="font-family: monospace">
                {{ row.last_commit?.slice(0, 7) }}
              </el-tag>
              <span v-else style="color: var(--text-muted)">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('common.actions')" width="260" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; gap: 4px" @click.stop>
                <el-button v-if="row.status !== 'running'" size="small" type="success" plain round @click="handleStart(row.id)">
                  {{ t('server.start') }}
                </el-button>
                <el-button v-if="row.status === 'running'" size="small" type="warning" plain round @click="handleStop(row.id)">
                  {{ t('server.stop') }}
                </el-button>
                <el-button v-if="row.status === 'running'" size="small" plain round @click="handleRestart(row.id)">
                  {{ t('server.restart') }}
                </el-button>
                <el-button v-if="row.github_url" size="small" type="info" plain round @click="handleUpdate(row.id)">
                  <el-icon><Refresh /></el-icon>
                </el-button>
                <el-button size="small" type="danger" plain round @click="handleDelete(row.id, row.name)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <AddServerDialog v-model="showAddDialog" @added="() => { showAddDialog = false; store.fetchServers() }" />
  </div>
</template>
