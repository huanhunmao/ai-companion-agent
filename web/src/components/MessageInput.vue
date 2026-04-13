<template>
  <div class="input-area">
    <textarea
      :value="inputValue"
      placeholder="输入你想说的话"
      @input="handleInput"
      @keydown.enter.exact.prevent="emit('send')"
    />
    <button :disabled="loading || !inputValue.trim()" @click="emit('send')">发送</button>
    <button v-if="loading" class="stop-btn" @click="emit('abort')">停止</button>
  </div>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    required: true,
  },
  inputValue: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update:inputValue', 'send', 'abort'])

const handleInput = event => {
  emit('update:inputValue', event.target.value)
}
</script>

<style scoped>
.input-area {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  align-items: stretch;
}

textarea {
  flex: 1;
  height: 96px;
  resize: none;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  padding: 12px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
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

.stop-btn {
  width: 100px;
  background: #ef4444;
}

@media (max-width: 960px) {
  .input-area {
    flex-direction: column;
  }

  textarea {
    height: 120px;
  }

  .input-area button,
  .stop-btn {
    width: 100%;
    min-height: 44px;
  }
}
</style>
