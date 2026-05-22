<template>
  <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0c1a2e 0%,#1a3a5c 100%);">
    <n-card style="width:400px;border-radius:12px;" :bordered="false" :content-style="{ padding: '32px' }">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="font-size:32px;font-weight:700;color:#001529;margin-bottom:4px;">
          <span style="color:#1890ff">◆</span> NetOps
        </div>
        <div style="color:#888;font-size:13px;">CMNET 网络运维管理平台</div>
      </div>

      <n-form @submit.prevent="handleLogin">
        <n-form-item label="用户名">
          <n-input v-model:value="username" placeholder="请输入用户名" size="large" :disabled="auth.loading">
            <template #prefix><n-icon><component :is="DesktopOutlined" /></n-icon></template>
          </n-input>
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="password" type="password" placeholder="请输入密码" size="large" show-password-on="click" :disabled="auth.loading" @keyup.enter="handleLogin" />
        </n-form-item>

        <n-alert v-if="error" type="error" closable @close="error = ''" style="margin-bottom:16px;">
          {{ error }}
        </n-alert>

        <n-button type="primary" block size="large" attr-type="submit" :loading="auth.loading" style="margin-top:8px;">
          登 录
        </n-button>
      </n-form>

      <div style="text-align:center;margin-top:20px;font-size:12px;color:#bbb;">
        <span>默认账号: admin / admin123</span>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DesktopOutlined } from '@vicons/antd'
import { auth } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const error = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败，请检查用户名和密码'
  }
}

onMounted(() => {
  if (auth.isAuthenticated) {
    router.push('/')
  }
})
</script>
