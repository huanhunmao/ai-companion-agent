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
        :persona-map="PERSONA_MAP"
        :persona-options="PERSONA_OPTIONS"
        :create-mode="createMode"
        @create="handleCreateSession"
        @switch="handleSwitchSession"
        @start-rename="handleStartRename"
        @rename="handleRenameSession"
        @toggle-pin="handleTogglePinSession"
        @delete="handleDeleteSession"
        @change-mode="handleChangeSessionMode"
        @update:editing-title="editingTitle = $event"
        @update:session-keyword="sessionKeyword = $event"
        @update:create-mode="createMode = $event"
      />

      <ChatPanel
        :current-messages="currentMessages"
        :loading="loading"
        :input-value="inputValue"
        :prompt-draft="promptDraft"
        :temperature-draft="temperatureDraft"
        :top-p-draft="topPDraft"
        :max-tokens-draft="maxTokensDraft"
        :memory-enabled-draft="memoryEnabledDraft"
        :model-options="MODEL_OPTIONS"
        :model-draft="modelDraft"
        :current-reply-meta="currentReplyMeta"
        :quoted-message="quotedMessage"
        :on-copy-message="copyMessage"
        :on-delete-message="handleDeleteMessage"
        :on-quote-message="handleQuoteMessage"
        :on-regenerate="handleRegenerate"
        :on-clear-quoted="clearQuotedMessage"
        @update:input-value="inputValue = $event"
        @update:prompt-draft="promptDraft = $event"
        @update:temperature-draft="temperatureDraft = $event"
        @update:top-p-draft="topPDraft = $event"
        @update:max-tokens-draft="maxTokensDraft = $event"
        @update:memory-enabled-draft="memoryEnabledDraft = $event"
        @update:model-draft="modelDraft = $event"
        @send="sendMessage"
        @abort="abortController?.abort()"
        @export="exportCurrentSession"
        @save-prompt="handleSavePrompt"
        @reset-prompt="handleResetPrompt"
        @use-prompt-template="handleUsePromptTemplate"
        @save-params="handleSaveParams"
        @save-memory-setting="handleSaveMemorySetting"
        @save-model-setting="handleSaveModelSetting"
      />

      <MemoryPanel
        :memory-list="memoryList"
        :memory-draft="memoryDraft"
        :editing-memory-index="editingMemoryIndex"
        :editing-memory-value="editingMemoryValue"
        @update:memory-draft="memoryDraft = $event"
        @update:editing-memory-value="editingMemoryValue = $event"
        @add="handleAddMemory"
        @delete="handleDeleteMemory"
        @start-edit="handleStartEditMemory"
        @save-edit="handleSaveEditMemory"
        @cancel-edit="handleCancelEditMemory"
      />
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import { createSession, loadSessions, saveSessions, sortSessions } from './utils/session'
import { PERSONA_MAP, PERSONA_OPTIONS } from './utils/persona'
import { MODEL_OPTIONS } from './utils/models'
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
const createMode = ref('companion')
const promptDraft = ref('')
const temperatureDraft = ref(0.7)
const topPDraft = ref(1)
const maxTokensDraft = ref(1200)
const quotedMessage = ref(null)
const memoryDraft = ref('')
const editingMemoryIndex = ref(-1)
const editingMemoryValue = ref('')
const memoryEnabledDraft = ref(true)
const modelDraft = ref(MODEL_OPTIONS[0].value)

const currentSession = computed(() => {
  return sessions.value.find(item => item.id === currentSessionId.value) || sessions.value[0]
})

const currentMessages = computed(() => currentSession.value?.messages || [])

const currentSystemPrompt = computed(() => {
  return currentSession.value?.customPrompt || ''
})

const currentParams = computed(() => {
  return {
    temperature: currentSession.value?.temperature ?? 0.7,
    topP: currentSession.value?.topP ?? 1,
    maxTokens: currentSession.value?.maxTokens ?? 1200,
  }
})

const currentMemoryEnabled = computed(() => {
  return currentSession.value?.memoryEnabled ?? true
})

const currentModel = computed(() => {
  return currentSession.value?.model || MODEL_OPTIONS[0].value
})

const currentReplyMeta = computed(() => {
  return currentSession.value?.lastReplyMeta || null
})

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
  const session = createSession(`新对话 ${sessions.value.length + 1}`, createMode.value)
  sessions.value = sortSessions([session, ...sessions.value])
  currentSessionId.value = session.id
}

const resetSystemMessageByMode = (messages = [], mode = 'companion', prompt) => {
  const persona = PERSONA_MAP[mode] || PERSONA_MAP.companion
  const finalPrompt = prompt || persona.systemPrompt
  const nextMessages = [...messages]

  const systemIndex = nextMessages.findIndex(item => item.role === 'system')
  if (systemIndex > -1) {
    nextMessages[systemIndex] = {
      ...nextMessages[systemIndex],
      content: finalPrompt,
    }
  } else {
    nextMessages.unshift({
      role: 'system',
      content: finalPrompt,
    })
  }

  return nextMessages
}

const handleChangeSessionMode = (id, mode) => {
  const persona = PERSONA_MAP[mode] || PERSONA_MAP.companion

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === id
        ? {
            ...item,
            mode,
            customPrompt: persona.systemPrompt,
            updatedAt: Date.now(),
            messages: resetSystemMessageByMode(item.messages, mode, persona.systemPrompt),
          }
        : item
    )
  )
}

const handleSavePrompt = () => {
  if (!currentSession.value) return

  const nextPrompt = promptDraft.value.trim()
  if (!nextPrompt) return

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            customPrompt: nextPrompt,
            updatedAt: Date.now(),
            messages: resetSystemMessageByMode(item.messages, item.mode, nextPrompt),
          }
        : item
    )
  )
}

const handleResetPrompt = () => {
  if (!currentSession.value) return

  const persona = PERSONA_MAP[currentSession.value.mode] || PERSONA_MAP.companion
  promptDraft.value = persona.systemPrompt

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            customPrompt: persona.systemPrompt,
            updatedAt: Date.now(),
            messages: resetSystemMessageByMode(item.messages, item.mode, persona.systemPrompt),
          }
        : item
    )
  )
}

const handleUsePromptTemplate = template => {
  promptDraft.value = template
}

const handleSaveParams = () => {
  if (!currentSession.value) return

  const nextTemperature = Math.min(2, Math.max(0, Number(temperatureDraft.value) || 0.7))
  const nextTopP = Math.min(1, Math.max(0, Number(topPDraft.value) || 1))
  const nextMaxTokens = Math.min(4000, Math.max(100, Number(maxTokensDraft.value) || 1200))

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            temperature: nextTemperature,
            topP: nextTopP,
            maxTokens: nextMaxTokens,
            updatedAt: Date.now(),
          }
        : item
    )
  )
}

const handleSaveMemorySetting = () => {
  if (!currentSession.value) return

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            memoryEnabled: !!memoryEnabledDraft.value,
            updatedAt: Date.now(),
          }
        : item
    )
  )
}

const handleSaveModelSetting = () => {
  if (!currentSession.value) return

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            model: modelDraft.value || MODEL_OPTIONS[0].value,
            updatedAt: Date.now(),
          }
        : item
    )
  )
}

const copyMessage = async content => {
  try {
    await navigator.clipboard.writeText(content || '')
    window.alert('消息已复制')
  } catch (e) {
    console.error(e)
    window.alert('复制失败')
  }
}

const handleDeleteMessage = index => {
  if (!currentSession.value) return

  if (quotedMessage.value) {
    if (quotedMessage.value.index === index) {
      quotedMessage.value = null
    } else if (quotedMessage.value.index > index) {
      quotedMessage.value = {
        ...quotedMessage.value,
        index: quotedMessage.value.index - 1,
      }
    }
  }

  const nextMessages = currentSession.value.messages.filter((_, i) => i !== index)

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            updatedAt: Date.now(),
            messages: nextMessages,
          }
        : item
    )
  )
}

const handleQuoteMessage = (item, index) => {
  quotedMessage.value = {
    index,
    role: item.role,
    content: item.content,
  }
}

const clearQuotedMessage = () => {
  quotedMessage.value = null
}

const handleRegenerate = async index => {
  if (!currentSession.value || loading.value) return

  const messages = [...currentSession.value.messages]
  const current = messages[index]
  const prev = messages[index - 1]

  if (!current || current.role !== 'assistant') return
  if (!prev || prev.role !== 'user') {
    window.alert('只能重新生成上一条 AI 回复')
    return
  }

  const nextMessages = messages.slice(0, index)

  sessions.value = sortSessions(
    sessions.value.map(item =>
      item.id === currentSessionId.value
        ? {
            ...item,
            updatedAt: Date.now(),
            messages: nextMessages,
          }
        : item
    )
  )

  loading.value = true
  try {
    await sendMessageStream(nextMessages)
  } catch (error) {
    updateCurrentSession(session => ({
      ...session,
      updatedAt: Date.now(),
      messages: [
        ...session.messages,
        {
          role: 'assistant',
          content: '重新生成失败，请稍后再试。',
        },
      ],
    }))
    console.error(error)
  } finally {
    loading.value = false
    abortController.value = null
  }
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

const saveMemories = async nextMemories => {
  if (!currentSessionId.value) return

  try {
    const res = await axios.put(`http://127.0.0.1:8080/api/memory/${currentSessionId.value}`, {
      memories: nextMemories,
    })
    memoryList.value = res.data.memories || []
  } catch (error) {
    console.error(error)
  }
}

const handleAddMemory = async () => {
  const text = memoryDraft.value.trim()
  if (!text) return

  await saveMemories([...memoryList.value, text])
  memoryDraft.value = ''
}

const handleDeleteMemory = async index => {
  const nextMemories = memoryList.value.filter((_, i) => i !== index)
  await saveMemories(nextMemories)

  if (editingMemoryIndex.value === index) {
    editingMemoryIndex.value = -1
    editingMemoryValue.value = ''
  }
}

const handleStartEditMemory = (item, index) => {
  editingMemoryIndex.value = index
  editingMemoryValue.value = item
}

const handleSaveEditMemory = async index => {
  const text = editingMemoryValue.value.trim()
  const nextMemories = [...memoryList.value]

  if (!text) {
    nextMemories.splice(index, 1)
  } else {
    nextMemories[index] = text
  }

  await saveMemories(nextMemories)
  editingMemoryIndex.value = -1
  editingMemoryValue.value = ''
}

const handleCancelEditMemory = () => {
  editingMemoryIndex.value = -1
  editingMemoryValue.value = ''
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

const buildMessagesForRequest = (messages = []) => {
  if (!quotedMessage.value) return messages

  const quoteRole =
    quotedMessage.value.role === 'user'
      ? '用户'
      : quotedMessage.value.role === 'assistant'
      ? 'AI'
      : quotedMessage.value.role

  const quotePrompt = [
    '以下是用户本次特别引用的一段历史消息，请你在回答时重点参考：',
    '',
    `引用角色：${quoteRole}`,
    `引用内容：${quotedMessage.value.content}`,
  ].join('\n')

  const nextMessages = [...messages]
  const systemIndex = nextMessages.findIndex(item => item.role === 'system')

  if (systemIndex > -1) {
    nextMessages[systemIndex] = {
      ...nextMessages[systemIndex],
      content: `${nextMessages[systemIndex].content}\n\n${quotePrompt}`,
    }
  } else {
    nextMessages.unshift({
      role: 'system',
      content: quotePrompt,
    })
  }

  return nextMessages
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
    const requestMessages = buildMessagesForRequest(currentSession.value.messages)
    await sendMessageStream(requestMessages)
    clearQuotedMessage()
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

  const cleanedMessages = (messages || []).filter(item => {
    if (!item) return false
    if (item.role !== 'assistant') return true
    return Boolean((item.content || '').trim())
  })

  const res = await fetch('http://127.0.0.1:8080/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: cleanedMessages,
      session_id: currentSession.value.id,
      model: currentSession.value.model,
      temperature: currentSession.value.temperature,
      top_p: currentSession.value.topP,
      max_tokens: currentSession.value.maxTokens,
      memory_enabled: currentSession.value.memoryEnabled,
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
          sessions.value = sortSessions(
            sessions.value.map(item =>
              item.id === currentSessionId.value
                ? {
                    ...item,
                    lastReplyMeta: payload.meta || null,
                    updatedAt: Date.now(),
                  }
                : item
            )
          )
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

watch(
  currentSystemPrompt,
  newVal => {
    promptDraft.value = newVal || ''
  },
  { immediate: true }
)

watch(
  currentParams,
  newVal => {
    temperatureDraft.value = newVal.temperature
    topPDraft.value = newVal.topP
    maxTokensDraft.value = newVal.maxTokens
  },
  { immediate: true, deep: true }
)

watch(
  currentMemoryEnabled,
  newVal => {
    memoryEnabledDraft.value = !!newVal
  },
  { immediate: true }
)

watch(
  currentModel,
  newVal => {
    modelDraft.value = newVal || MODEL_OPTIONS[0].value
  },
  { immediate: true }
)

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