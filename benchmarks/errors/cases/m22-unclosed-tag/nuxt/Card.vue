<script setup lang="ts">
defineProps<{
  title: string
  count: number
}>()

defineEmits<{
  hide: []
}>()
</script>

<template>
  <article class="card">
    <h2>{{ title }}: {{ count }} tasks</h2>
    <footer>
      <slot name="footer" />
    <button type="button" @click="$emit('hide')">Hide</button>
  </article>
</template>
