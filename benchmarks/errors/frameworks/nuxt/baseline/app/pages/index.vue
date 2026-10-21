<script setup lang="ts">
const config = useRuntimeConfig()
const route = useRoute()
const { data: board } = await useFetch('/api/board')

const count = ref(board.value?.count ?? 0)
const open = ref(false)
const hidden = ref<string[]>([])
// The text typed into the search field so far.
const query = ref('')

// Every card inside reads the board's name with inject(), so none takes it as a prop.
provide('boardName', 'Projects')

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
    <h1>Projects</h1>
    <p>Owned by {{ board?.owner.name }}</p>
    <div id="board" class="board" title="Board">
      <img
        src="/avatar.svg"
        :alt="board?.owner.name"
        width="32"
        height="32"
      >
      <p>Owner: {{ board?.owner.name }}</p>
      <p>Projects: {{ board?.cards.length }}</p>
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

      <!-- The form submits back to this page with its text in `q`. -->
      <form role="search">
        <input
          v-model="query"
          type="search"
          name="q"
        >
        <button type="submit">Search</button>
        <p>Searching for: {{ query }}</p>
      </form>
      <p v-if="route.query.q">Searched: {{ route.query.q }}</p>

      <nav>
        <NuxtLink to="/about">About</NuxtLink>
        <NuxtLink to="/projects/1">Project 1</NuxtLink>
      </nav>
    </div>
  </div>
</template>

<style>
/* The server picks the heading color and sends it with the board data. */
h1 {
  color: v-bind('board?.accent');
}
</style>
