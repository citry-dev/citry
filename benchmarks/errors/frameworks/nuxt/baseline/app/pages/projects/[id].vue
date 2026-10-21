<script setup lang="ts">
// The project id is a number. A file-based route cannot declare a type, so
// the page checks the id with route validation, as Nuxt's routing docs
// show; any other value gets Nuxt's 404 page. With typed pages on, the
// route's params are typed for every page, so the check first narrows
// them to this page's `id`.
definePageMeta({
  validate: (route) => {
    return 'id' in route.params && /^\d+$/.test(route.params.id)
  },
})

const route = useRoute()
</script>

<template>
  <h1>Project {{ route.params.id }}</h1>
</template>
