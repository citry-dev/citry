<script setup lang="ts">
defineProps<{
  open: boolean
}>()

// The details panel owns `open`; the status line only asks it to close.
defineEmits<{
  close: []
}>()
</script>

<template>
  <p>
    Status: {{ open ? 'open' : 'closed' }}
    <button type="button" @click="$emit('close')">Close</button>
  </p>
</template>
