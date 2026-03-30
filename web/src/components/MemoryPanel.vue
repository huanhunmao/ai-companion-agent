<template>
  <aside class="memory-panel">
    <div class="memory-header">会话记忆</div>
    <div v-if="memoryList.length" class="memory-list">
      <div v-for="(item, index) in memoryList" :key="index" class="memory-item">
        {{ item }}
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
})
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
</style>
