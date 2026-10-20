<script setup lang="ts">
const config = useRuntimeConfig()
const { data: board } = await useFetch('/api/board')

const count = ref(board.value?.count ?? 0)
const open = ref(false)
const hidden = ref<string[]>([])

const visibleCards = computed(() =>
  (board.value?.cards ?? []).filter((card) => !hidden.value.includes(card.title)),
)

async function add() {
  const result = await $fetch('/api/save', {
    method: 'POST',
    body: { amount: 1 },
  })
  count.value = result.count
}

function toggleDetails() {
  open.value = !open.value
}

function hide(title: string) {
  hidden.value.push(title)
}
</script>

<template>
  <div>
    <NuxtRouteAnnouncer />
    <h1>Projects</h1>
    <div class="board" title="Board">
      <p>Owner: {{ board?.owner.name }}</p>
      <p>API: {{ config.public.apiBase }}</p>

      <Card
        v-for="card in visibleCards"
        :key="card.title"
        :title="card.title"
        :count="card.count"
        :tone="card.featured ? 'accent' : 'plain'"
        @hide="hide(card.title)"
      >
        <template #footer="footer">
          <a :href="`#${card.title.toLowerCase()}`">Open {{ footer.title }} ({{ footer.count }})</a>
        </template>
      </Card>

      <p>Saved: {{ count }}</p>
      <button type="button" @click="add">Add</button>

      <button type="button" :aria-expanded="open" @click="toggleDetails">
        Details
      </button>
      <p v-if="open">Details are visible</p>
      <Status :open="open" @close="open = false" />

      <form role="search">
        <button type="submit">Search</button>
      </form>
    </div>
  </div>
</template>
