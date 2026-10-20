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
    </footer>
    <button type="button" @click="$emit('hdie')">Hide</button>
  </article>
</template>
