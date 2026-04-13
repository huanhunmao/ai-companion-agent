<template>
  <main class="main">
    <div class="main-header">
      <h1>AI Companion Agent</h1>
      <ExportActions @export="emit('export', $event)" />
    </div>

    <div class="prompt-panel">
      <div class="prompt-panel-header">
        <div class="prompt-panel-title">Prompt Playground</div>
        <div class="prompt-panel-actions">
          <button class="prompt-btn secondary" @click="emit('reset-prompt')">恢复默认</button>
          <button class="prompt-btn" @click="emit('save-prompt')">保存 Prompt</button>
        </div>
      </div>

      <textarea
        :value="promptDraft"
        class="prompt-textarea"
        placeholder="编辑当前会话的 system prompt"
        @input="emit('update:promptDraft', $event.target.value)"
      />

      <div class="prompt-template-list">
        <span
          class="prompt-template-tag"
          @click="emit('use-prompt-template', '你是一个专业、友好、清晰的 AI 助手，回答准确，表达简洁。')"
        >
          通用助手
        </span>
        <span
          class="prompt-template-tag"
          @click="
            emit(
              'use-prompt-template',
              '你是一个资深技术顾问，回答时要结构化、专业、可执行，优先给出步骤、代码和避坑建议。'
            )
          "
        >
          技术顾问模板
        </span>
        <span
          class="prompt-template-tag"
          @click="
            emit(
              'use-prompt-template',
              '你是一个资深面试教练，请从面试官视角给出高质量回答，突出考点、答题框架和表达建议。'
            )
          "
        >
          面试教练模板
        </span>
        <span
          class="prompt-template-tag"
          @click="emit('use-prompt-template', '你是一个温柔、稳定、善于倾听和鼓励的陪伴型 AI，回答自然、真诚、有情绪价值。')"
        >
          陪伴模板
        </span>
      </div>
    </div>

    <div class="params-panel">
      <div class="params-panel-header">
        <div class="params-panel-title">聊天参数</div>
        <button class="prompt-btn" @click="emit('save-params')">保存参数</button>
      </div>

      <div class="params-grid">
        <div class="param-item">
          <label class="param-label">model</label>

          <select
            :value="modelDraft"
            class="param-input"
            @change="emit('update:modelDraft', $event.target.value)"
          >
            <option v-for="item in modelOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>

          <div class="memory-switch-row">
            <button class="prompt-btn small" @click="emit('save-model-setting')">保存模型设置</button>
          </div>

          <div class="param-tip">不同会话可绑定不同模型提供方（只配置了 Moonshot 测试考虑为了成本💰）</div>
        </div>

        <div class="param-item">
          <label class="param-label">temperature</label>
          <input
            :value="temperatureDraft"
            class="param-input"
            type="number"
            min="0"
            max="2"
            step="0.1"
            @input="emit('update:temperatureDraft', $event.target.value)"
          />
          <div class="param-tip">越高越发散，越低越稳定</div>
        </div>

        <div class="param-item">
          <label class="param-label">top_p</label>
          <input
            :value="topPDraft"
            class="param-input"
            type="number"
            min="0"
            max="1"
            step="0.1"
            @input="emit('update:topPDraft', $event.target.value)"
          />
          <div class="param-tip">控制采样范围</div>
        </div>

        <div class="param-item">
          <label class="param-label">max_tokens</label>
          <input
            :value="maxTokensDraft"
            class="param-input"
            type="number"
            min="100"
            max="4000"
            step="100"
            @input="emit('update:maxTokensDraft', $event.target.value)"
          />
          <div class="param-tip">限制单次最大输出长度</div>
        </div>

        <div class="param-item">
          <label class="param-label">memory</label>

          <div class="memory-switch-row">
            <label class="memory-switch-label">
              <input
                :checked="memoryEnabledDraft"
                type="checkbox"
                @change="emit('update:memoryEnabledDraft', $event.target.checked)"
              />
              <span>{{ memoryEnabledDraft ? '开启记忆注入' : '关闭记忆注入' }}</span>
            </label>

            <button class="prompt-btn small" @click="emit('save-memory-setting')">保存记忆设置</button>
          </div>

          <div class="param-tip">关闭后会保留记忆数据，但不会注入到对话上下文</div>
        </div>
      </div>
    </div>

    <div v-if="currentReplyMeta" class="reply-meta-bar">
      <div class="reply-meta-item">
        <span class="reply-meta-label">模型</span>
        <span class="reply-meta-value">{{ currentReplyMeta.model || '-' }}</span>
      </div>
      <div class="reply-meta-item">
        <span class="reply-meta-label">提供方</span>
        <span class="reply-meta-value">{{ currentReplyMeta.provider || '-' }}</span>
      </div>
      <div class="reply-meta-item">
        <span class="reply-meta-label">耗时</span>
        <span class="reply-meta-value">{{ currentReplyMeta.duration_ms }} ms</span>
      </div>
      <div class="reply-meta-item">
        <span class="reply-meta-label">时间</span>
        <span class="reply-meta-value">
          {{ new Date(currentReplyMeta.reply_at).toLocaleString() }}
        </span>
      </div>
    </div>

    <MessageList
      :current-messages="currentMessages"
      :loading="loading"
      :on-copy-message="onCopyMessage"
      :on-delete-message="onDeleteMessage"
      :on-quote-message="onQuoteMessage"
      :on-regenerate="onRegenerate"
    />

    <div v-if="quotedMessage" class="quote-bar">
      <div class="quote-content">
        <span class="quote-label">
          正在引用 {{ quotedMessage.role === 'user' ? '用户' : 'AI' }} 消息：
        </span>
        <span class="quote-text">{{ quotedMessage.content }}</span>
      </div>
      <span class="quote-close" @click="onClearQuoted">取消</span>
    </div>

    <MessageInput
      :loading="loading"
      :input-value="inputValue"
      @update:input-value="emit('update:inputValue', $event)"
      @send="emit('send')"
      @abort="emit('abort')"
    />
  </main>
</template>

<script setup>
import ExportActions from './ExportActions.vue'
import MessageInput from './MessageInput.vue'
import MessageList from './MessageList.vue'

const props = defineProps({
  currentMessages: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    required: true,
  },
  inputValue: {
    type: String,
    required: true,
  },
  promptDraft: {
    type: String,
    required: true,
  },
  temperatureDraft: {
    type: [Number, String],
    required: true,
  },
  topPDraft: {
    type: [Number, String],
    required: true,
  },
  maxTokensDraft: {
    type: [Number, String],
    required: true,
  },
  memoryEnabledDraft: {
    type: Boolean,
    required: true,
  },
  modelOptions: {
    type: Array,
    required: true,
  },
  modelDraft: {
    type: String,
    required: true,
  },
  currentReplyMeta: {
    type: Object,
    default: null,
  },
  quotedMessage: {
    type: Object,
    default: null,
  },
  onCopyMessage: {
    type: Function,
    required: true,
  },
  onDeleteMessage: {
    type: Function,
    required: true,
  },
  onQuoteMessage: {
    type: Function,
    required: true,
  },
  onRegenerate: {
    type: Function,
    required: true,
  },
  onClearQuoted: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'update:inputValue',
  'send',
  'abort',
  'export',
  'update:promptDraft',
  'save-prompt',
  'reset-prompt',
  'use-prompt-template',
  'update:temperatureDraft',
  'update:topPDraft',
  'update:maxTokensDraft',
  'update:memoryEnabledDraft',
  'update:modelDraft',
  'save-params',
  'save-memory-setting',
  'save-model-setting',
])
</script>

<style scoped>
.main {
  flex: 1;
  min-width: 0;
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-sizing: border-box;
  height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.main-header h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.2;
  color: #111827;
  font-weight: 700;
}

.prompt-panel {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  max-height: 260px;
  overflow: auto;
}

.prompt-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.prompt-panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.prompt-panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-btn {
  border: none;
  border-radius: 10px;
  background: #111827;
  color: #fff;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
}

.prompt-btn.secondary {
  background: #6b7280;
}

.prompt-textarea {
  width: 100%;
  min-height: 72px;
  max-height: 140px;
  resize: vertical;
  box-sizing: border-box;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  outline: none;
  background: #fff;
  margin-bottom: 12px;
}

.prompt-template-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.prompt-template-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  font-size: 12px;
  cursor: pointer;
}

.prompt-template-tag:hover {
  background: #e0e7ff;
}

.params-panel {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  max-height: 240px;
  overflow: auto;
}

.params-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.params-panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.param-item {
  padding: 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.param-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}

.param-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
  outline: none;
  background: #fff;
}

.param-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

.memory-switch-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.memory-switch-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #111827;
}

.prompt-btn.small {
  padding: 6px 10px;
  font-size: 12px;
}

.reply-meta-bar {
  margin-bottom: 12px;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f8fafc;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
}

.reply-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.reply-meta-label {
  font-size: 12px;
  color: #6b7280;
}

.reply-meta-value {
  font-size: 13px;
  color: #111827;
  font-weight: 500;
  word-break: break-all;
}

.quote-bar {
  margin-top: 8px;
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid #dbeafe;
  background: #eff6ff;
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.quote-content {
  min-width: 0;
  flex: 1;
}

.quote-label {
  font-size: 12px;
  color: #1d4ed8;
  margin-right: 6px;
}

.quote-text {
  font-size: 13px;
  color: #1f2937;
  word-break: break-word;
}

.quote-close {
  flex-shrink: 0;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
}

.quote-close:hover {
  color: #111827;
}

@media (max-width: 1200px) {
  .params-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-header h1 {
    font-size: 32px;
  }
}

@media (max-width: 960px) {
  .main {
    width: 100%;
    height: auto;
    min-height: calc(100vh - 104px);
    padding: 16px;
  }

  .main-header,
  .prompt-panel-header,
  .params-panel-header,
  .quote-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .main-header h1 {
    font-size: 26px;
  }

  .prompt-panel-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .params-grid {
    grid-template-columns: 1fr;
  }

  .prompt-btn {
    min-height: 40px;
  }
}
</style>
