<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { McpServer, McpTool, LogEntry } from '../types'
import { serverApi } from '../api/mcp'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const serverId = Number(route.params.id)

const server = ref<McpServer | null>(null)
const tools = ref<McpTool[]>([])
const logs = ref<LogEntry[]>([])
const activeTab = ref('tools')
const loading = ref(false)
const editMode = ref(false)

const editForm = ref({
  name: '',
  command: '',
  args: '',
  auto_update: true,
  auto_restart: true,
  env: [] as { key: string; value: string }[],
})

let eventSource: EventSource | null = null

onMounted(async () => {
  await fetchServer()
  await fetchTools()
})

onUnmounted(() => { eventSource?.close() })

async function fetchServer() {
  loading.value = true
  try {
    const res = await serverApi.get(serverId)
    server.value = res.data
  } finally { loading.value = false }
}

async function fetchTools() {
  try {
    const res = await serverApi.getTools(serverId)
    tools.value = res.data
  } catch { /* server may not be running */ }
}

async function fetchLogs() {
  const res = await serverApi.getLogs(serverId)
  logs.value = res.data
}

function startLogStream() {
  eventSource?.close()
  eventSource = new EventSource(`/api/servers/${serverId}/logs/stream`)
  eventSource.onmessage = (event) => {
    const entry = JSON.parse(event.data)
    logs.value.push(entry)
    if (logs.value.length > 500) logs.value.shift()
  }
}

function handleTabChange(tab: string) {
  if (tab === 'logs') { fetchLogs(); startLogStream() }
  else { eventSource?.close(); eventSource = null }
}

function startEdit() {
  if (!server.value) return
  editForm.value = {
    name: server.value.name,
    command: server.value.command,
    args: (server.value.args || []).join(' '),
    auto_update: server.value.auto_update,
    auto_restart: server.value.auto_restart,
    env: Object.entries(server.value.env || {}).map(([key, value]) => ({ key, value })),
  }
  editMode.value = true
}

async function saveEdit() {
  const envDict: Record<string, string> = {}
  for (const item of editForm.value.env) { if (item.key) envDict[item.key] = item.value }
  await serverApi.update(serverId, {
    name: editForm.value.name,
    command: editForm.value.command,
    args: editForm.value.args ? editForm.value.args.split(' ') : [],
    auto_update: editForm.value.auto_update,
    auto_restart: editForm.value.auto_restart,
    env: envDict,
  })
  ElMessage.success(t('detail.configSaved'))
  editMode.value = false
  await fetchServer()
}
</script>

<template>
  <div v-loading="loading">
    <!-- Back Button & Title -->
    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px">
      <el-button circle plain @click="router.push('/servers')">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div v-if="server" style="display: flex; align-items: center; gap: 12px">
        <div style="width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 600"
          :style="{ background: server.project_type === 'python' ? '#EEF2FF' : '#FFF7ED', color: server.project_type === 'python' ? '#4F6EF7' : '#EA580C' }"
        >
          {{ server.project_type === 'python' ? 'Py' : 'JS' }}
        </div>
        <div>
          <h3 style="font-size: 18px; font-weight: 600">{{ server.name }}</h3>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px">
            {{ server.github_url || server.local_path }}
          </div>
        </div>
        <span class="status-badge" :class="server.status" style="margin-left: 8px">
          {{ server.status === 'running' ? t('server.statusRunning') : server.status === 'stopped' ? t('server.statusStopped') : t('server.statusError') }}
        </span>
      </div>
    </div>

    <!-- Info Cards -->
    <div class="grid-4" style="margin-bottom: 24px" v-if="server">
      <div class="stat-card" style="padding: 16px 20px">
        <div class="stat-info">
          <div class="stat-label">{{ t('server.command') }}</div>
          <div style="font-size: 14px; font-weight: 500; margin-top: 4px; font-family: monospace">
            {{ server.command }} {{ (server.args || []).join(' ') }}
          </div>
        </div>
      </div>
      <div class="stat-card" style="padding: 16px 20px">
        <div class="stat-info">
          <div class="stat-label">{{ t('server.toolsCount') }}</div>
          <div style="font-size: 24px; font-weight: 700; margin-top: 4px; color: var(--primary)">
            {{ server.tools_count }}
          </div>
        </div>
      </div>
      <div class="stat-card" style="padding: 16px 20px">
        <div class="stat-info">
          <div class="stat-label">{{ t('server.commit') }}</div>
          <div style="font-size: 14px; font-weight: 500; margin-top: 4px; font-family: monospace">
            {{ server.last_commit?.slice(0, 8) || '-' }}
          </div>
        </div>
      </div>
      <div class="stat-card" style="padding: 16px 20px">
        <div class="stat-info">
          <div class="stat-label">{{ t('server.autoUpdate') }} / {{ t('server.autoRestart') }}</div>
          <div style="display: flex; gap: 8px; margin-top: 6px">
            <el-tag :type="server.auto_update ? 'success' : 'info'" size="small" effect="plain" round>
              {{ t('server.autoUpdate') }}: {{ server.auto_update ? 'ON' : 'OFF' }}
            </el-tag>
            <el-tag :type="server.auto_restart ? 'success' : 'info'" size="small" effect="plain" round>
              {{ t('server.autoRestart') }}: {{ server.auto_restart ? 'ON' : 'OFF' }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" style="padding: 0 24px">
        <!-- Tools Tab -->
        <el-tab-pane :label="t('detail.tabs.tools')" name="tools">
          <el-table :data="tools" stripe style="margin: 0 -24px; width: calc(100% + 48px)"
            :header-cell-style="{ background: '#F8FAFC', fontWeight: 600, fontSize: '13px' }"
          >
            <el-table-column :label="t('detail.toolName')" min-width="220">
              <template #default="{ row }">
                <span style="font-family: monospace; font-size: 13px; color: var(--primary); font-weight: 500">
                  {{ row.name }}
                </span>
              </template>
            </el-table-column>
            <el-table-column :label="t('detail.originalName')" width="160">
              <template #default="{ row }">
                <span style="font-family: monospace; font-size: 13px">{{ row.original_name }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('detail.description')" min-width="300" show-overflow-tooltip>
              <template #default="{ row }">
                <span style="color: var(--text-secondary); font-size: 13px">{{ row.description }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="t('detail.parameters')" width="120" align="center">
              <template #default="{ row }">
                <el-popover trigger="click" width="450">
                  <template #reference>
                    <el-button size="small" plain round>
                      <el-icon><View /></el-icon>
                    </el-button>
                  </template>
                  <pre style="max-height: 320px; overflow: auto; font-size: 12px; font-family: 'SF Mono', monospace; background: #F8FAFC; padding: 12px; border-radius: 8px">{{ JSON.stringify(row.input_schema, null, 2) }}</pre>
                </el-popover>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Config Tab -->
        <el-tab-pane :label="t('detail.tabs.config')" name="config">
          <div style="padding: 16px 0">
            <div v-if="!editMode">
              <el-button type="primary" plain round @click="startEdit">
                <el-icon style="margin-right: 6px"><Edit /></el-icon>
                {{ t('detail.editConfig') }}
              </el-button>
            </div>
            <el-form v-else label-position="top" style="max-width: 560px">
              <el-form-item :label="t('server.serverName')">
                <el-input v-model="editForm.name" size="large" />
              </el-form-item>
              <div style="display: flex; gap: 12px">
                <el-form-item :label="t('server.command')" style="flex: 1">
                  <el-input v-model="editForm.command" size="large" />
                </el-form-item>
                <el-form-item :label="t('server.arguments')" style="flex: 1">
                  <el-input v-model="editForm.args" size="large" />
                </el-form-item>
              </div>
              <div style="display: flex; gap: 24px; margin-bottom: 16px">
                <el-form-item :label="t('server.autoUpdate')">
                  <el-switch v-model="editForm.auto_update" />
                </el-form-item>
                <el-form-item :label="t('server.autoRestart')">
                  <el-switch v-model="editForm.auto_restart" />
                </el-form-item>
              </div>
              <el-form-item :label="t('server.envVars')">
                <div style="width: 100%">
                  <div v-for="(item, i) in editForm.env" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px">
                    <el-input v-model="item.key" placeholder="KEY" />
                    <el-input v-model="item.value" placeholder="VALUE" />
                    <el-button type="danger" plain @click="editForm.env.splice(i, 1)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                  <el-button size="small" plain @click="editForm.env.push({ key: '', value: '' })">
                    <el-icon><Plus /></el-icon> {{ t('addDialog.addEnvVar') }}
                  </el-button>
                </div>
              </el-form-item>
              <div style="display: flex; gap: 8px; margin-top: 8px">
                <el-button type="primary" round @click="saveEdit">{{ t('detail.saveConfig') }}</el-button>
                <el-button round @click="editMode = false">{{ t('detail.cancelEdit') }}</el-button>
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Logs Tab -->
        <el-tab-pane :label="t('detail.tabs.logs')" name="logs">
          <div class="log-terminal" style="margin: 0 -24px 0 -24px; border-radius: 0">
            <div v-for="(log, i) in logs" :key="i" class="log-line">
              <span class="log-time">{{ log.timestamp?.split('T')[1]?.slice(0, 8) || log.timestamp }}</span>
              <span class="log-msg">{{ log.message }}</span>
            </div>
            <div v-if="!logs.length" style="color: #475569; text-align: center; padding: 60px 0">
              {{ t('detail.noLogs') }}
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
