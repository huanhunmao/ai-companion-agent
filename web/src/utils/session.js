import { PERSONA_MAP } from './persona'
import { MODEL_OPTIONS } from './models'

export const STORAGE_KEY = 'ai-companion-sessions'

export function createSession(title = '新对话', mode = 'companion') {
  const persona = PERSONA_MAP[mode] || PERSONA_MAP.companion

  return {
    id: crypto.randomUUID(),
    title,
    mode,
    customPrompt: persona.systemPrompt,
    model: MODEL_OPTIONS[0].value,
    temperature: 0.7,
    topP: 1,
    maxTokens: 1200,
    memoryEnabled: true,
    lastReplyMeta: null,
    pinned: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [
      {
        role: 'system',
        content: persona.systemPrompt,
      },
      {
        role: 'assistant',
        content: '你好，我已经准备好了。你今天想聊什么？',
      },
    ],
  }
}

export function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      const first = createSession()
      saveSessions([first])
      return [first]
    }
    const sessions = JSON.parse(raw)
    if (!Array.isArray(sessions) || !sessions.length) {
      const first = createSession()
      saveSessions([first])
      return [first]
    }
    
    const normalized = sessions.map(item => {
      const mode = item.mode || 'companion'
      const persona = PERSONA_MAP[mode] || PERSONA_MAP.companion

      return {
        mode,
        customPrompt:
          item.customPrompt ||
          item.messages?.find(m => m.role === 'system')?.content ||
          persona.systemPrompt,
        model: MODEL_OPTIONS[0].value,
        temperature: 0.7,
        topP: 1,
        maxTokens: 1200,
        memoryEnabled: true,
        lastReplyMeta: null,
        pinned: false,
        ...item,
      }
    })
    return sortSessions(normalized)
  } catch (e) {
    const first = createSession()
    saveSessions([first])
    return [first]
  }
}

export function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}

export function sortSessions(list = []) {
  return [...list].sort((a, b) => {
    const aPinned = a.pinned ? 1 : 0
    const bPinned = b.pinned ? 1 : 0

    if (aPinned !== bPinned) {
      return bPinned - aPinned
    }

    return (b.updatedAt || 0) - (a.updatedAt || 0)
  })
}