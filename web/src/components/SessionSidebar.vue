<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2>会话</h2>
      <button class="new-btn" @click="emit('create')">+ 新建</button>
    </div>

    <input
      :value="sessionKeyword"
      class="session-search"
      placeholder="搜索会话标题或消息内容"
      @input="handleKeywordInput"
    />

    <div class="session-list">
      <div
        v-for="item in sessions"
        :key="item.id"
        :class="['session-item', currentSessionId === item.id ? 'active' : '']"
        @click="emit('switch', item.id)"
      >
        <div class="session-top">
          <template v-if="editingSessionId === item.id">
            <input
              :value="editingTitle"
              class="session-input"
              @input="handleEditingTitleInput"
              @click.stop
              @keydown.enter="emit('rename', item.id)"
              @blur="emit('rename', item.id)"
            />
          </template>
          <template v-else>
            <div class="session-title-row">
              <div class="session-title">{{ item.title }}</div>
              <span v-if="item.pinned" class="pin-badge">置顶</span>
            </div>
          </template>

          <div class="session-actions">
            <span class="action-btn" @click.stop="emit('toggle-pin', item.id)">
              {{ item.pinned ? '取消置顶' : '置顶' }}
            </span>
            <span class="action-btn" @click.stop="emit('start-rename', item)">改名</span>
            <span class="action-btn delete" @click.stop="emit('delete', item.id)">删除</span>
          </div>
        </div>
        <div class="session-time">{{ formatTime(item.updatedAt) }}</div>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  sessions: {
    type: Array,
    required: true,
  },
  currentSessionId: {
    type: String,
    required: true,
  },
  editingSessionId: {
    type: String,
    required: true,
  },
  editingTitle: {
    type: String,
    required: true,
  },
  sessionKeyword: {
    type: String,
    required: true,
  },
  formatTime: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits([
  'create',
  'switch',
  'start-rename',
  'rename',
  'toggle-pin',
  'delete',
  'update:editingTitle',
  'update:sessionKeyword',
])

const handleEditingTitleInput = event => {
  emit('update:editingTitle', event.target.value)
}

const handleKeywordInput = event => {
  emit('update:sessionKeyword', event.target.value)
}
</script>

<style scoped>
.sidebar {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-sizing: border-box;
  height: calc(100vh - 48px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
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

.session-search {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  margin-bottom: 12px;
}

.session-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
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

.session-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.session-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.session-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
}

.pin-badge {
  flex-shrink: 0;
  font-size: 10px;
  line-height: 1;
  padding: 4px 6px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
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

.session-time {
  font-size: 12px;
  color: #6b7280;
}
</style>
