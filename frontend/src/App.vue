<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLanguage } from './i18n'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const auth = useAuthStore()

const currentPath = computed(() => route.path)
const isLoginPage = computed(() => route.name === 'Login')
const showUserMenu = computed(() => auth.authEnabled && auth.token)

function switchLang(lang: string) {
  setLanguage(lang)
}

function navigateTo(path: string) {
  router.push(path)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <!-- Top Navbar (hidden on login page) -->
  <nav v-if="!isLoginPage" class="top-navbar">
    <div class="navbar-brand" @click="navigateTo('/')">
      <div class="brand-icon">G</div>
      <span class="brand-text">{{ t('nav.title') }}</span>
    </div>

    <div class="navbar-center">
      <button
        class="nav-pill"
        :class="{ active: currentPath === '/' }"
        @click="navigateTo('/')"
      >
        <el-icon class="nav-pill-icon"><DataAnalysis /></el-icon>
        {{ t('nav.dashboard') }}
      </button>
      <button
        class="nav-pill"
        :class="{ active: currentPath.startsWith('/servers') }"
        @click="navigateTo('/servers')"
      >
        <el-icon class="nav-pill-icon"><Monitor /></el-icon>
        {{ t('nav.servers') }}
      </button>
      <button
        class="nav-pill"
        :class="{ active: currentPath === '/settings' }"
        @click="navigateTo('/settings')"
      >
        <el-icon class="nav-pill-icon"><Setting /></el-icon>
        {{ t('nav.settings') }}
      </button>
    </div>

    <div class="navbar-right">
      <div class="lang-switch">
        <button :class="{ active: locale === 'zh' }" @click="switchLang('zh')">中文</button>
        <button :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
      </div>
      <template v-if="showUserMenu">
        <el-dropdown trigger="click" @command="handleLogout">
          <div class="user-badge">
            <el-icon><User /></el-icon>
            <span>{{ auth.username }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>{{ t('auth.logout') }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </div>
  </nav>

  <!-- Page Content -->
  <router-view />
</template>

<style scoped>
.user-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-full);
  background: var(--border-light);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.user-badge:hover {
  background: var(--border);
  color: var(--text-primary);
}
</style>
