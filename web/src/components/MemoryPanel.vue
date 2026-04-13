<template>
  <aside class="memory-panel">
    <div class="memory-header">会话记忆</div>

    <div class="memory-editor">
      <input
        :value="memoryDraft"
        class="memory-input"
        placeholder="手动新增一条记忆"
        @input="emit('update:memoryDraft', $event.target.value)"
        @keydown.enter="emit('add')"
      />
      <button class="memory-add-btn" @click="emit('add')">新增</button>
    </div>

    <div v-if="memoryList.length" class="memory-list">
      <div v-for="(item, index) in memoryList" :key="index" class="memory-item">
        <template v-if="editingMemoryIndex === index">
          <input
            :value="editingMemoryValue"
            class="memory-edit-input"
            @input="emit('update:editingMemoryValue', $event.target.value)"
            @keydown.enter="emit('save-edit', index)"
            @keydown.esc="emit('cancel-edit')"
          />
          <div class="memory-actions">
            <span class="memory-action" @click="emit('save-edit', index)">保存</span>
            <span class="memory-action delete" @click="emit('cancel-edit')">取消</span>
          </div>
        </template>

        <template v-else>
          <div class="memory-text">{{ item }}</div>
          <div class="memory-actions">
            <span class="memory-action" @click="emit('start-edit', item, index)">编辑</span>
            <span class="memory-action delete" @click="emit('delete', index)">删除</span>
          </div>
        </template>
      </div>
    </div>

    <div v-else class="memory-empty">暂时还没有提取到长期记忆</div>
  </aside>
</template>

<script setup>
defineProps({
  memoryList: {
    type: Array,
    required: true,
  },
  memoryDraft: {
    type: String,
    required: true,
  },
  editingMemoryIndex: {
    type: Number,
    required: true,
  },
  editingMemoryValue: {
    type: String,
    required: true,
  },
})

const emit = defineEmits([
  'update:memoryDraft',
  'update:editingMemoryValue',
  'add',
  'delete',
  'start-edit',
  'save-edit',
  'cancel-edit',
])
</script>

<style scoped>
.memory-panel {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-sizing: border-box;
  height: calc(100vh - 48px);
  overflow-y: auto;
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
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

.memory-editor {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.memory-input,
.memory-edit-input {
  flex: 1;
  min-width: 0;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
  background: #fff;
}

.memory-add-btn {
  border: none;
  border-radius: 10px;
  background: #111827;
  color: #fff;
  padding: 0 14px;
  cursor: pointer;
  flex-shrink: 0;
}

.memory-text {
  line-height: 1.6;
  color: #111827;
  word-break: break-word;
}

.memory-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.memory-action {
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  user-select: none;
}

.memory-action:hover {
  color: #111827;
}

.memory-action.delete:hover {
  color: #dc2626;
}

@media (max-width: 960px) {
  .memory-panel {
    width: 100%;
    height: auto;
    min-height: calc(100vh - 104px);
  }

  .memory-editor {
    flex-direction: column;
  }

  .memory-add-btn {
    height: 44px;
  }
}
</style>
