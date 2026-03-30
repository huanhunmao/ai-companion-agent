<template>
  <div class="export-actions">
    <button class="export-btn" @click="emit('export', 'md')">导出 Markdown</button>
    <button class="export-btn secondary" @click="emit('export', 'json')">导出 JSON</button>
  </div>
</template>

<script setup>
const emit = defineEmits(['export'])
</script>

<style scoped>
.export-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.export-btn {
  border: none;
  border-radius: 10px;
  background: #111827;
  color: #fff;
  padding: 10px 14px;
  font-size: 13px;
  cursor: pointer;
}

.export-btn.secondary {
  background: #4b5563;
}
</style>
