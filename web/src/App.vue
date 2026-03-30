<template>
  <div class="page">
    <div class="container">
      <SessionSidebar
        :sessions="filteredSessions"
        :current-session-id="currentSessionId"
        :editing-session-id="editingSessionId"
        :editing-title="editingTitle"
        :session-keyword="sessionKeyword"
        :format-time="formatTime"
        @create="handleCreateSession"
        @switch="handleSwitchSession"
        @start-rename="handleStartRename"
        @rename="handleRenameSession"
        @toggle-pin="handleTogglePinSession"
        @delete="handleDeleteSession"
        @update:editing-title="editingTitle = $event"
        @update:session-keyword="sessionKeyword = $event"
      />

      <ChatPanel
        :current-messages="currentMessages"
        :loading="loading"
        :input-value="inputValue"
        @update:input-value="inputValue = $event"
        @send="sendMessage"
        @abort="abortController?.abort()"
        @export="exportCurrentSession"
      />

      <MemoryPanel :memory-list="memoryList" />
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import { createSession, loadSessions, saveSessions, sortSessions } from './utils/session'
import SessionSidebar from './components/SessionSidebar.vue'
import ChatPanel from './components/ChatPanel.vue'
import MemoryPanel from './components/MemoryPanel.vue'

const inputValue = ref('')
const loading = ref(false)
const abortController = ref(null)

const sessions = ref(loadSessions())
const currentSessionId = ref(sessions.value[0]?.id || '')
const memoryList = ref([])
const editingSessionId = ref('')
const editingTitle = ref('')
const sessionKeyword = ref('')

const currentSession = computed(() => {
  return sessions.value.find(item => item.id === currentSessionId.value) || sessions.value[0]
})

const currentMessages = computed(() => currentSession.value?.messages || [])

const filteredSessions = computed(() => {
  const keyword = sessionKeyword.value.trim().toLowerCase()
  if (!keyword) return sessions.value

  return sessions.value.filter(item => {
    const titleMatch = (item.title || '').toLowerCase().includes(keyword)
    const messageMatch = (item.messages || []).some(msg =>
      (msg.content || '').toLowerCase().includes(keyword)
    )
    return titleMatch || messageMatch
  })
})

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
  sessions.value = sortSessions(
    sessions.value.map(item => {
      if (item.id !== currentSessionId.value) return item
      return updater(item)
    })
  )
}

const handleCreateSession = () => {
  const session = createSession(`新对话 ${sessions.value.length + 1}`)
  sessions.value = sortSessions([session, ...sessions.value])
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

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === id
        ? {
            ...item,
            title,
            updatedAt: Date.now(),
          }
        : item
    )
  )

  editingSessionId.value = ''
  editingTitle.value = ''
}

const handleTogglePinSession = id => {
  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === id
        ? {
            ...item,
            pinned: !item.pinned,
          }
        : item
    )
  )
}

const handleDeleteSession = async id => {
  if (sessions.value.length === 1) {
    window.alert('至少保留一个会话')
    return
  }

  const ok = window.confirm('确认删除这个会话吗？删除后记忆也会一起清除。')
  if (!ok) return

  try {
    await axios.delete(`http://127.0.0.1:8080/api/session/${id}`)
  } catch (error) {
    console.error(error)
  }

  const nextSessions = sortSessions(sessions.value.filter(item => item.id !== id))
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
    const res = await axios.get(`http://127.0.0.1:8080/api/memory/${currentSessionId.value}`)
    memoryList.value = res.data.memories || []
  } catch (error) {
    memoryList.value = []
    console.error(error)
  }
}

const downloadFile = (filename, content, type = 'text/plain;charset=utf-8') => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const exportCurrentSession = format => {
  if (!currentSession.value) return

  const session = currentSession.value
  const safeTitle = (session.title || '未命名会话').replace(/[\\/:*?"<>|]/g, '-')
  const time = formatTime(session.updatedAt).replace(/[ :]/g, '-')

  if (format === 'json') {
    downloadFile(
      `${safeTitle}-${time}.json`,
      JSON.stringify(session, null, 2),
      'application/json;charset=utf-8'
    )
    return
  }

  if (format === 'md') {
    const lines = [
      `# ${session.title || '未命名会话'}`,
      '',
      `- 会话ID：${session.id}`,
      `- 更新时间：${new Date(session.updatedAt).toLocaleString()}`,
      '',
      '---',
      '',
    ]

    session.messages.forEach(item => {
      if (item.role === 'system') return

      const roleName =
        item.role === 'user'
          ? '我'
          : item.role === 'assistant'
          ? 'AI'
          : item.role

      lines.push(`## ${roleName}`)
      lines.push('')
      lines.push(item.content || '')
      lines.push('')
    })

    if (memoryList.value.length) {
      lines.push('---')
      lines.push('')
      lines.push('## 会话记忆')
      lines.push('')
      memoryList.value.forEach(item => {
        lines.push(`- ${item}`)
      })
      lines.push('')
    }

    downloadFile(
      `${safeTitle}-${time}.md`,
      lines.join('\n'),
      'text/markdown;charset=utf-8'
    )
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

  const res = await fetch('http://127.0.0.1:8080/api/chat/stream', {
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
  display: flex;
}
.container {
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  gap: 20px;
  align-items: stretch;
}
</style>