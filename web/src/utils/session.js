export const STORAGE_KEY = 'ai-companion-sessions'

export function createSession(title = '新对话') {
  return {
    id: crypto.randomUUID(),
    title,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [
      {
        role: 'system',
        content: '你是一个温柔、聪明、会长期陪伴用户的AI伙伴。',
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
    return sessions
  } catch (e) {
    const first = createSession()
    saveSessions([first])
    return [first]
  }
}

export function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}