<script setup lang="ts">
defineProps<{
  title: string
  count: number
  tone: 'plain' | 'accent'
}>()

defineEmits<{
  hide: []
}>()
</script>

<template>
  <article :class="['card', `card--${tone}`]">
    <h2>{{ title }}: {{ count }} tasks</h2>
    <footer>
      <!-- The card hands its title and count to the page's footer fill. -->
      <slot
        name="footer"
        :title="title"
        :count="count"
      />
    </footer>
    <button type="button" @click="$emit('hide')">Hide</button>
  </article>
</template>

<style scoped>
.card--accent {
  border: 2px solid rgb(0, 0, 255);
}
</style>
