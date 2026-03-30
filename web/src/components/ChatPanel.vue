<template>
  <main class="main">
    <div class="main-header">
      <h1>AI Companion Agent</h1>
      <ExportActions @export="emit('export', $event)" />
    </div>

    <MessageList :current-messages="currentMessages" :loading="loading" />
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
})

const emit = defineEmits(['update:inputValue', 'send', 'abort', 'export'])
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
</style>
