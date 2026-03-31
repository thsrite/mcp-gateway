import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { McpServer, SystemInfo } from '../types'
import { serverApi, systemApi } from '../api/mcp'

export const useMcpStore = defineStore('mcp', () => {
  const servers = ref<McpServer[]>([])
  const systemInfo = ref<SystemInfo | null>(null)
  const loading = ref(false)

  async function fetchServers() {
    loading.value = true
    try {
      const res = await serverApi.list()
      servers.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchSystemInfo() {
    const res = await systemApi.info()
    systemInfo.value = res.data
  }

  return { servers, systemInfo, loading, fetchServers, fetchSystemInfo }
})
