<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setLanguage } from './i18n'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const currentPath = computed(() => route.path)

const pageTitle = computed(() => {
  if (route.name === 'Dashboard') return t('nav.dashboard')
  if (route.name === 'ServerList') return t('nav.servers')
  if (route.name === 'ServerDetail') return t('detail.basicInfo')
  if (route.name === 'Settings') return t('nav.settings')
  return ''
})

function switchLang(lang: string) {
  setLanguage(lang)
}

function navigateTo(path: string) {
  router.push(path)
}
</script>

<template>
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-icon">G</div>
      <span class="logo-text">{{ t('nav.title') }}</span>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-group-title">MENU</div>
      <div
        class="nav-item"
        :class="{ active: currentPath === '/' }"
        @click="navigateTo('/')"
      >
        <el-icon class="nav-icon"><DataAnalysis /></el-icon>
        <span>{{ t('nav.dashboard') }}</span>
      </div>
      <div
        class="nav-item"
        :class="{ active: currentPath.startsWith('/servers') }"
        @click="navigateTo('/servers')"
      >
        <el-icon class="nav-icon"><Monitor /></el-icon>
        <span>{{ t('nav.servers') }}</span>
      </div>
      <div
        class="nav-item"
        :class="{ active: currentPath === '/settings' }"
        @click="navigateTo('/settings')"
      >
        <el-icon class="nav-icon"><Setting /></el-icon>
        <span>{{ t('nav.settings') }}</span>
      </div>
    </nav>

    <!-- Bottom version info -->
    <div style="padding: 16px 20px; border-top: 1px solid rgba(255,255,255,0.08)">
      <div style="color: rgba(255,255,255,0.3); font-size: 11px; text-align: center">
        v0.1.0
      </div>
    </div>
  </aside>

  <!-- Main Content -->
  <div class="main-content">
    <header class="main-header">
      <div class="header-left">
        <h2>{{ pageTitle }}</h2>
      </div>
      <div class="header-right">
        <div class="lang-switch">
          <button :class="{ active: locale === 'zh' }" @click="switchLang('zh')">中文</button>
          <button :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
        </div>
      </div>
    </header>
    <div class="page-content">
      <router-view />
    </div>
  </div>
</template>
