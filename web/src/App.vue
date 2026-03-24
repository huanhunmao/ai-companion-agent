<template>
  <div class="page">
    <div class="container">
      <aside class="sidebar">
        <div class="sidebar-header">
          <h2>会话</h2>
          <button class="new-btn" @click="handleCreateSession">+ 新建</button>
        </div>

        <div
            v-for="item in sessions"
            :key="item.id"
            :class="['session-item', currentSessionId === item.id ? 'active' : '']"
            @click="handleSwitchSession(item.id)"
            >
            <div class="session-top">
                <template v-if="editingSessionId === item.id">
                <input
                    v-model="editingTitle"
                    class="session-input"
                    @click.stop
                    @keydown.enter="handleRenameSession(item.id)"
                    @blur="handleRenameSession(item.id)"
                />
                </template>
                <template v-else>
                <div class="session-title">{{ item.title }}</div>
                </template>

                <div class="session-actions">
                <span class="action-btn" @click.stop="handleStartRename(item)">改名</span>
                <span class="action-btn delete" @click.stop="handleDeleteSession(item.id)">删除</span>
                </div>
            </div>
            <div class="session-time">{{ formatTime(item.updatedAt) }}</div>
         </div>
      </aside>

      <main class="main">
        <h1>AI Companion Agent</h1>

        <div class="chat-box">
          <div
            v-for="(item, index) in currentMessages"
            :key="index"
            :class="['msg', item.role]"
          >
            <div class="role">
              {{
                item.role === 'user'
                  ? '我'
                  : item.role === 'assistant'
                  ? 'AI'
                  : 'system'
              }}
            </div>
            <div class="content">{{ item.content }}</div>
          </div>

          <div v-if="loading" class="msg assistant">
            <div class="role">AI</div>
            <div class="content">思考中...</div>
          </div>
        </div>

        <div class="input-area">
          <textarea
            v-model="inputValue"
            placeholder="输入你想说的话"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <button :disabled="loading || !inputValue.trim()" @click="sendMessage">
            发送
            </button>
            <button
            v-if="loading"
            class="stop-btn"
            @click="abortController?.abort()"
            >
            停止
            </button>
        </div>
      </main>

      <aside class="memory-panel">
        <div class="memory-header">会话记忆</div>
        <div v-if="memoryList.length" class="memory-list">
            <div v-for="(item, index) in memoryList" :key="index" class="memory-item">
            {{ item }}
            </div>
        </div>
        <div v-else class="memory-empty">暂时还没有提取到长期记忆</div>
        </aside>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import { createSession, loadSessions, saveSessions } from './utils/session'

const inputValue = ref('')
const loading = ref(false)
const abortController = ref(null)

const sessions = ref(loadSessions())
const currentSessionId = ref(sessions.value[0]?.id || '')
const memoryList = ref([])
const editingSessionId = ref('')
const editingTitle = ref('')

const currentSession = computed(() => {
  return sessions.value.find(item => item.id === currentSessionId.value) || sessions.value[0]
})

const currentMessages = computed(() => currentSession.value?.messages || [])

watch(
  sessions,
  newVal => {
    saveSessions(newVal)
  },
  { deep: true }
)

const formatTime = timestamp => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const MM = `${date.getMonth() + 1}`.padStart(2, '0')
  const DD = `${date.getDate()}`.padStart(2, '0')
  const HH = `${date.getHours()}`.padStart(2, '0')
  const mm = `${date.getMinutes()}`.padStart(2, '0')
  return `${MM}-${DD} ${HH}:${mm}`
}

const updateCurrentSession = updater => {
  sessions.value = sessions.value.map(item => {
    if (item.id !== currentSessionId.value) return item
    return updater(item)
  })
}

const handleCreateSession = () => {
  const session = createSession(`新对话 ${sessions.value.length + 1}`)
  sessions.value = [session, ...sessions.value]
  currentSessionId.value = session.id
}

const handleSwitchSession = id => {
  currentSessionId.value = id
}

const handleStartRename = item => {
  editingSessionId.value = item.id
  editingTitle.value = item.title
}

const handleRenameSession = id => {
  const title = editingTitle.value.trim()
  if (!title) {
    editingSessionId.value = ''
    editingTitle.value = ''
    return
  }

  sessions.value = sessions.value.map(item =>
    item.id === id
      ? {
          ...item,
          title,
          updatedAt: Date.now(),
        }
      : item
  )

  editingSessionId.value = ''
  editingTitle.value = ''
}

const handleDeleteSession = async id => {
  if (sessions.value.length === 1) {
    window.alert('至少保留一个会话')
    return
  }

  const ok = window.confirm('确认删除这个会话吗？删除后记忆也会一起清除。')
  if (!ok) return

  try {
    await axios.delete(`http://127.0.0.1:8000/api/session/${id}`)
  } catch (error) {
    console.error(error)
  }

  const nextSessions = sessions.value.filter(item => item.id !== id)
  sessions.value = nextSessions

  if (currentSessionId.value === id) {
    currentSessionId.value = nextSessions[0]?.id || ''
    await nextTick()
    fetchMemories()
  }
}

const fetchMemories = async () => {
  if (!currentSessionId.value) return
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/memory/${currentSessionId.value}`)
    memoryList.value = res.data.memories || []
  } catch (error) {
    memoryList.value = []
    console.error(error)
  }
}

const sendMessage = async () => {
  const text = inputValue.value.trim()
  if (!text || loading.value || !currentSession.value) return

  updateCurrentSession(session => ({
    ...session,
    updatedAt: Date.now(),
    title:
      session.messages.filter(i => i.role === 'user').length === 0
        ? text.slice(0, 12)
        : session.title,
    messages: [
      ...session.messages,
      {
        role: 'user',
        content: text,
      },
    ],
  }))

  inputValue.value = ''
  loading.value = true

  try {
    await sendMessageStream(currentSession.value.messages)
  } catch (error) {
    updateCurrentSession(session => ({
      ...session,
      updatedAt: Date.now(),
      messages: [
        ...session.messages,
        {
          role: 'assistant',
          content: '请求失败，请检查后端或API Key配置。',
        },
      ],
    }))
    console.error(error)
  } finally {
    loading.value = false
    abortController.value = null
  }
}

const sendMessageStream = async messages => {
  abortController.value = new AbortController()

  const res = await fetch('http://127.0.0.1:8000/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      session_id: currentSession.value.id,
    }),
    signal: abortController.value.signal,
  })

  if (!res.ok || !res.body) {
    throw new Error('流式请求失败')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  updateCurrentSession(session => ({
    ...session,
    updatedAt: Date.now(),
    messages: [
      ...session.messages,
      {
        role: 'assistant',
        content: '',
      },
    ],
  }))

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue

      const jsonText = line.slice(6)
      if (!jsonText) continue

      try {
        const payload = JSON.parse(jsonText)

        if (payload.type === 'chunk') {
          updateCurrentSession(session => {
            const nextMessages = [...session.messages]
            const lastIndex = nextMessages.length - 1
            const lastMessage = nextMessages[lastIndex]

            if (lastMessage?.role === 'assistant') {
              nextMessages[lastIndex] = {
                ...lastMessage,
                content: (lastMessage.content || '') + payload.content,
              }
            }

            return {
              ...session,
              updatedAt: Date.now(),
              messages: nextMessages,
            }
          })
        }

        if (payload.type === 'error') {
          updateCurrentSession(session => {
            const nextMessages = [...session.messages]
            const lastIndex = nextMessages.length - 1
            const lastMessage = nextMessages[lastIndex]

            if (lastMessage?.role === 'assistant') {
              nextMessages[lastIndex] = {
                ...lastMessage,
                content: payload.content,
              }
            }

            return {
              ...session,
              updatedAt: Date.now(),
              messages: nextMessages,
            }
          })
        }

        if (payload.type === 'done') {
          await fetchMemories()
        }
      } catch (e) {
        console.error('stream parse error:', e)
      }
    }
  }
}

watch(currentSessionId, () => {
  fetchMemories()
})

onMounted(() => {
  fetchMemories()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f7fb;
  padding: 24px;
  box-sizing: border-box;
}
.container {
  width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
}
.sidebar {
  width: 280px;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-sizing: border-box;
  height: calc(100vh - 48px);
  overflow: hidden;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
}
.new-btn {
  border: none;
  border-radius: 10px;
  background: #111827;
  color: #fff;
  padding: 8px 12px;
  cursor: pointer;
}
.session-list {
  overflow-y: auto;
  height: calc(100% - 50px);
}
.session-item {
  padding: 12px;
  border-radius: 12px;
  background: #f9fafb;
  cursor: pointer;
  margin-bottom: 10px;
  border: 1px solid transparent;
}
.session-item.active {
  border-color: #cbd5e1;
  background: #eef2ff;
}
.session-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
}
.session-time {
  font-size: 12px;
  color: #6b7280;
}
.main {
  flex: 1;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-sizing: border-box;
}
h1 {
  margin: 0 0 20px;
}
.chat-box {
  height: 520px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: #fafafa;
}
.msg {
  margin-bottom: 16px;
}
.msg.system {
  display: none;
}
.role {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}
.content {
  display: inline-block;
  max-width: 75%;
  line-height: 1.7;
  padding: 12px 14px;
  border-radius: 12px;
  word-break: break-word;
}
.user .content {
  background: #dbeafe;
}
.assistant .content {
  background: #f3f4f6;
}
.input-area {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}
textarea {
  flex: 1;
  min-height: 100px;
  resize: vertical;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  padding: 12px;
  font-size: 14px;
  outline: none;
}
button {
  border: none;
  border-radius: 12px;
  background: #111827;
  color: #fff;
  cursor: pointer;
}
.input-area button {
  width: 100px;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.memory-panel {
  width: 280px;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-sizing: border-box;
  height: calc(100vh - 48px);
  overflow-y: auto;
}
.memory-header {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
}
.memory-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.memory-item {
  padding: 12px;
  border-radius: 12px;
  background: #f9fafb;
  line-height: 1.6;
  color: #111827;
  border: 1px solid #e5e7eb;
}
.memory-empty {
  color: #6b7280;
  font-size: 14px;
}
.session-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.session-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
}

.action-btn:hover {
  color: #111827;
}

.action-btn.delete:hover {
  color: #dc2626;
}

.session-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}
</style>