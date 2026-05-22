<template>
  <n-card title="凭据管理">
    <n-space style="margin-bottom:12px;">
      <n-button type="primary" @click="showCreateModal = true">+ 新增凭据</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="credentialList" :bordered="false" :loading="loading" :pagination="pagination" />

    <!-- Create / Edit Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" :title="editingId ? '编辑凭据' : '新增凭据'" style="width:480px" :bordered="false">
      <n-form :model="form" label-placement="left" label-width="80">
        <n-form-item label="名称" required>
          <n-input v-model:value="form.name" placeholder="例如: 默认SSH凭据" />
        </n-form-item>
        <n-form-item label="用户名" required>
          <n-input v-model:value="form.username" placeholder="SSH 登录用户名" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" :placeholder="editingId ? '留空则不修改' : 'SSH 密码'" show-password-on="click" />
        </n-form-item>
        <n-form-item label="认证类型">
          <n-select v-model:value="form.auth_type" :options="authOptions" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="saveCredential" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Delete Confirm -->
    <n-modal v-model:show="showDeleteConfirm" preset="dialog" title="确认删除" type="warning"
      :content="`确定要删除凭据「${deleteTarget?.name}」吗？引用此凭据的设备将无法自动连接。`"
      positive-text="删除" negative-text="取消"
      @positive-click="confirmDelete"
      @negative-click="showDeleteConfirm = false" />
  </n-card>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, useMessage } from 'naive-ui'
import { credentialApi } from '../api'

const message = useMessage()
const loading = ref(false)
const credentialList = ref([])
const showCreateModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const showDeleteConfirm = ref(false)
const deleteTarget = ref(null)

const form = ref({
  name: '',
  username: '',
  password: '',
  auth_type: 'password',
})

const authOptions = [
  { label: '密码', value: 'password' },
  { label: '密钥', value: 'key' },
]

const pagination = { pageSize: 10 }

onMounted(() => loadCredentials())

async function loadCredentials() {
  loading.value = true
  try {
    const { data } = await credentialApi.list()
    credentialList.value = data || []
  } catch {
    message.error('加载凭据列表失败')
  } finally {
    loading.value = false
  }
}

function openEdit(cred) {
  editingId.value = cred.id
  form.value = {
    name: cred.name,
    username: cred.username,
    password: '',
    auth_type: cred.auth_type,
  }
  showCreateModal.value = true
}

function openCreate() {
  editingId.value = null
  form.value = { name: '', username: '', password: '', auth_type: 'password' }
  showCreateModal.value = true
}

async function saveCredential() {
  saving.value = true
  try {
    if (editingId.value) {
      await credentialApi.update(editingId.value, form.value)
      message.success('凭据已更新')
    } else {
      await credentialApi.create(form.value)
      message.success('凭据已创建')
    }
    showCreateModal.value = false
    loadCredentials()
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function confirmDelete() {
  if (!deleteTarget.value) return
  credentialApi.delete(deleteTarget.value.id)
    .then(() => {
      message.success('凭据已删除')
      loadCredentials()
    })
    .catch((e) => {
      message.error(e.response?.data?.detail || '删除失败')
    })
    .finally(() => {
      showDeleteConfirm.value = false
      deleteTarget.value = null
    })
}

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '名称', key: 'name', width: 140 },
  { title: '用户名', key: 'username', width: 120 },
  {
    title: '密码', key: 'has_password', width: 70,
    render: (r) => r.has_password ? '********' : '-',
  },
  {
    title: '认证类型', key: 'auth_type', width: 90,
    render: (r) => h(NTag, { bordered: false, size: 'small' }, r.auth_type === 'password' ? '密码' : '密钥'),
  },
  {
    title: '创建时间', key: 'created_at', width: 170,
    render: (r) => r.created_at ? new Date(r.created_at).toLocaleString() : '-',
  },
  {
    title: '操作', width: 120,
    render: (r) => h(NSpace, null, [
      h(NButton, { size: 'tiny', quaternary: true, onClick: () => openEdit(r) }, '编辑'),
      h(NButton, { size: 'tiny', quaternary: true, type: 'error', onClick: () => { deleteTarget.value = r; showDeleteConfirm.value = true } }, '删除'),
    ]),
  },
]
</script>
