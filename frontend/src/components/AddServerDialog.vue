<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { serverApi } from '../api/mcp'

const { t } = useI18n()
defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue', 'added'])

const activeTab = ref('github')
const loading = ref(false)

const githubForm = reactive({
  github_url: '',
  name: '',
  branch: '',
  env: [] as { key: string; value: string }[],
})

const manualForm = reactive({
  name: '',
  command: '',
  args: '',
  local_path: '',
  env: [] as { key: string; value: string }[],
})

function envToDict(envList: { key: string; value: string }[]): Record<string, string> {
  const result: Record<string, string> = {}
  for (const item of envList) {
    if (item.key) result[item.key] = item.value
  }
  return result
}

async function handleSubmit() {
  loading.value = true
  try {
    if (activeTab.value === 'github') {
      if (!githubForm.github_url) {
        ElMessage.warning(t('common.required'))
        return
      }
      await serverApi.create({
        github_url: githubForm.github_url,
        name: githubForm.name || undefined,
        branch: githubForm.branch || undefined,
        env: envToDict(githubForm.env),
      })
    } else {
      if (!manualForm.name || !manualForm.command || !manualForm.local_path) {
        ElMessage.warning(t('common.required'))
        return
      }
      await serverApi.create({
        name: manualForm.name,
        command: manualForm.command,
        args: manualForm.args ? manualForm.args.split(' ') : [],
        local_path: manualForm.local_path,
        env: envToDict(manualForm.env),
      })
    }
    ElMessage.success(t('addDialog.addSuccess'))
    emit('added')
    resetForms()
  } catch { /* interceptor handles */ } finally {
    loading.value = false
  }
}

function resetForms() {
  githubForm.github_url = ''
  githubForm.name = ''
  githubForm.branch = ''
  githubForm.env = []
  manualForm.name = ''
  manualForm.command = ''
  manualForm.args = ''
  manualForm.local_path = ''
  manualForm.env = []
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('addDialog.title')"
    width="580px"
    @close="emit('update:modelValue', false)"
    destroy-on-close
  >
    <el-tabs v-model="activeTab" style="margin-top: -8px">
      <el-tab-pane :label="t('addDialog.fromGithub')" name="github">
        <el-form label-position="top" style="margin-top: 12px">
          <el-form-item :label="t('server.githubUrl')" required>
            <el-input
              v-model="githubForm.github_url"
              :placeholder="t('addDialog.githubUrlPlaceholder')"
              prefix-icon="Link"
              size="large"
            />
          </el-form-item>
          <div style="display: flex; gap: 12px">
            <el-form-item :label="t('server.serverName')" style="flex: 1">
              <el-input v-model="githubForm.name" :placeholder="t('addDialog.namePlaceholder')" size="large" />
            </el-form-item>
            <el-form-item :label="t('addDialog.branch')" style="flex: 1">
              <el-input v-model="githubForm.branch" :placeholder="t('addDialog.branchPlaceholder')" size="large" />
            </el-form-item>
          </div>
          <el-form-item :label="t('server.envVars')">
            <div style="width: 100%">
              <div v-for="(item, i) in githubForm.env" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px">
                <el-input v-model="item.key" placeholder="KEY" />
                <el-input v-model="item.value" placeholder="VALUE" />
                <el-button type="danger" plain :icon="'Delete'" @click="githubForm.env.splice(i, 1)" />
              </div>
              <el-button size="small" plain @click="githubForm.env.push({ key: '', value: '' })">
                <el-icon><Plus /></el-icon> {{ t('addDialog.addEnvVar') }}
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      <el-tab-pane :label="t('addDialog.manual')" name="manual">
        <el-form label-position="top" style="margin-top: 12px">
          <el-form-item :label="t('server.serverName')" required>
            <el-input v-model="manualForm.name" placeholder="my-mcp-server" size="large" />
          </el-form-item>
          <div style="display: flex; gap: 12px">
            <el-form-item :label="t('server.command')" required style="flex: 1">
              <el-input v-model="manualForm.command" :placeholder="t('addDialog.commandPlaceholder')" size="large" />
            </el-form-item>
            <el-form-item :label="t('server.arguments')" style="flex: 1">
              <el-input v-model="manualForm.args" :placeholder="t('addDialog.argsPlaceholder')" size="large" />
            </el-form-item>
          </div>
          <el-form-item :label="t('server.localPath')" required>
            <el-input v-model="manualForm.local_path" :placeholder="t('addDialog.localPathPlaceholder')" size="large" />
          </el-form-item>
          <el-form-item :label="t('server.envVars')">
            <div style="width: 100%">
              <div v-for="(item, i) in manualForm.env" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px">
                <el-input v-model="item.key" placeholder="KEY" />
                <el-input v-model="item.value" placeholder="VALUE" />
                <el-button type="danger" plain :icon="'Delete'" @click="manualForm.env.splice(i, 1)" />
              </div>
              <el-button size="small" plain @click="manualForm.env.push({ key: '', value: '' })">
                <el-icon><Plus /></el-icon> {{ t('addDialog.addEnvVar') }}
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button round @click="emit('update:modelValue', false)">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" round :loading="loading" @click="handleSubmit">
        {{ loading ? t('addDialog.adding') : activeTab === 'github' ? t('addDialog.cloneAndAdd') : t('common.add') }}
      </el-button>
    </template>
  </el-dialog>
</template>
