<template>
  <div ref="chatBoxRef" class="chat-box">
    <div v-for="(item, index) in currentMessages" :key="index" :class="['msg', item.role]">
      <div class="role-row">
        <div class="role">{{ getRoleLabel(item.role) }}</div>

        <div v-if="item.role !== 'system'" class="msg-actions">
          <span class="msg-action-btn" @click="onCopyMessage?.(item.content)">复制</span>
          <span class="msg-action-btn delete" @click="onDeleteMessage?.(index)">删除</span>
          <span
            v-if="item.role === 'assistant'"
            class="msg-action-btn"
            @click="onRegenerate?.(index)"
          >
            重新生成
          </span>
        </div>
      </div>
      <div
        v-if="item.role === 'assistant'"
        class="content markdown-body"
        v-html="renderMarkdown(item.content)"
      />
      <div v-else class="content">{{ item.content }}</div>
    </div>

    <div v-if="loading" class="msg assistant">
      <div class="role">AI</div>
      <div class="content">思考中...</div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  currentMessages: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
  onCopyMessage: {
    type: Function,
    required: true,
  },
  onDeleteMessage: {
    type: Function,
    required: true,
  },
  onRegenerate: {
    type: Function,
    required: true,
  },
})

const chatBoxRef = ref(null)

const copyCode = async code => {
  try {
    await navigator.clipboard.writeText(code || '')
    window.alert('代码已复制')
  } catch (error) {
    console.error(error)
    window.alert('复制失败')
  }
}

const renderer = new marked.Renderer()
renderer.code = ({ text, lang }) => {
  const language = lang || 'text'
  const escapedCode = (text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

  return `
    <div class="code-block-wrap">
      <div class="code-block-header">
        <span class="code-lang">${language}</span>
        <button class="copy-code-btn" data-code="${escapedCode}">复制</button>
      </div>
      <pre><code class="language-${language}">${escapedCode}</code></pre>
    </div>
  `
}

const renderMarkdown = content => {
  const rawHtml = marked.parse(content || '', { renderer })
  return DOMPurify.sanitize(rawHtml)
}

const getRoleLabel = role => {
  if (role === 'user') return '我'
  if (role === 'assistant') return 'AI'
  return 'system'
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
  }
}

const handleChatBoxClick = event => {
  const target = event.target
  if (target?.classList?.contains('copy-code-btn')) {
    const code = target.getAttribute('data-code') || ''
    copyCode(
      code
        .replace(/&quot;/g, '"')
        .replace(/&gt;/g, '>')
        .replace(/&lt;/g, '<')
        .replace(/&amp;/g, '&')
    )
  }
}

watch(
  () => props.currentMessages.length,
  () => {
    scrollToBottom()
  }
)

watch(
  () => props.currentMessages[props.currentMessages.length - 1]?.content,
  () => {
    scrollToBottom()
  }
)

watch(
  () => props.loading,
  () => {
    scrollToBottom()
  }
)

onMounted(() => {
  scrollToBottom()
  if (chatBoxRef.value) {
    chatBoxRef.value.addEventListener('click', handleChatBoxClick)
  }
})

onUnmounted(() => {
  if (chatBoxRef.value) {
    chatBoxRef.value.removeEventListener('click', handleChatBoxClick)
  }
})
</script>

<style scoped>
.chat-box {
  flex: 1;
  min-height: 0;
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

.role-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.msg-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.msg-action-btn {
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  user-select: none;
}

.msg-action-btn:hover {
  color: #111827;
}

.msg-action-btn.delete:hover {
  color: #dc2626;
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

.markdown-body :deep(p) {
  margin: 0 0 8px;
}

.markdown-body :deep(pre) {
  background: #111827;
  color: #f9fafb;
  padding: 12px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 13px;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 10px 0 8px;
  font-size: 16px;
}

.markdown-body :deep(blockquote) {
  margin: 8px 0;
  padding-left: 12px;
  border-left: 4px solid #d1d5db;
  color: #4b5563;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 8px;
  text-align: left;
}

.code-block-wrap {
  margin: 8px 0;
}

.code-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1f2937;
  color: #f9fafb;
  padding: 8px 12px;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  font-size: 12px;
}

.code-lang {
  opacity: 0.9;
}

.copy-code-btn {
  border: none;
  background: #374151;
  color: #fff;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
}

.copy-code-btn:hover {
  background: #4b5563;
}

.markdown-body :deep(.code-block-wrap pre) {
  margin: 0;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}
</style>
