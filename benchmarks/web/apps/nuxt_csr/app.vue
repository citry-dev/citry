<script setup>
const route = useRoute();
const count = Number(route.query.count || 14);
const session = String(route.query.session || "manual");
const {data: initial, error} = await useFetch("/api/initial", {
  query: {count, session},
  key: `project-board:${session}:${count}`,
});
const board = ref(initial.value?.board || null);
const csrf = ref(initial.value?.csrf || "");
const pending = ref(0);
const activeTab = ref("outputs");
const disclosureOpen = ref(false);

async function ready() {
  await nextTick();
  if (!board.value || pending.value) return;
  window.__citryBench?.ready({
    session: board.value.session,
    operation: board.value.operation,
    revision: board.value.revision,
    pending: pending.value,
    phase: board.value.revision === 0 ? "initial" : "update",
  });
}

onMounted(ready);

async function submit(event) {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.currentTarget));
  pending.value += 1;
  let updated = false;
  try {
    const result = await $fetch("/api/action", {
      method: "POST",
      headers: {"x-csrf-token": csrf.value},
      body: {...values, csrf: csrf.value},
    });
    board.value = {...result.board, session, csrf: csrf.value};
    updated = true;
  } catch (submitError) {
    console.error(submitError);
  } finally {
    pending.value -= 1;
    if (updated) await ready();
  }
}

function formKey(name, revision) {
  return `${name}-${revision}`;
}
</script>

<template>
  <p v-if="error">Unable to load the project board.</p>
  <template v-else-if="board">
    <aside id="local-disclosure">
      <button type="button" data-bench-action="disclosure" :aria-expanded="disclosureOpen" @click="disclosureOpen = !disclosureOpen">Local details</button>
      <p id="disclosure-content" :hidden="!disclosureOpen">This disclosure needs no server request.</p>
      <label for="preserved-input">Local draft</label><input id="preserved-input" value="Unchanged draft">
    </aside>
    <section id="board" :data-project-id="board.project.id" :data-session="board.session" :data-operation="board.operation" :data-revision="board.revision" :data-visible-count="board.visible_count" :data-total-count="board.total_count">
      <div class="project-shell">
        <nav id="project-navbar" aria-label="Primary"><a href="#board">Projects</a><span aria-current="page">{{ board.project.name }}</span></nav>
        <aside id="project-sidebar">
          <section aria-labelledby="bookmark-heading"><h2 id="bookmark-heading">Project Bookmarks</h2><a v-for="bookmark in board.bookmarks" :key="bookmark.id" :data-bookmark-id="bookmark.id" :data-bookmark-name="bookmark.text" :href="bookmark.url"><span class="bookmark-name">{{ bookmark.text }}</span></a></section>
          <nav aria-label="Project phases"><h2>Phases</h2><ul><li v-for="phase in board.phase_groups" :key="phase.id"><a :href="`#phase-${phase.id}`">{{ phase.title }}</a></li></ul></nav>
        </aside>
        <main>
          <header class="project-header"><p><a href="#project-navbar" aria-label="Projects home">Home</a> / {{ board.project.name }}</p><h1 id="board-title">{{ board.title }}</h1><p><span id="project-start-date">{{ board.project.start_date }}</span> – <span id="project-end-date">{{ board.project.end_date }}</span></p><p>Status: <span id="project-status">{{ board.project.status }}</span>; organization: <span id="project-organization">{{ board.project.organization }}</span></p><p><span id="visible-count">{{ board.visible_count }}</span> visible outputs</p></header>
          <section aria-label="Project actions">
            <div class="toolbar">
              <form @submit="submit" novalidate><input type="hidden" name="session" :value="board.session"><input type="hidden" name="csrf" :value="csrf"><input type="hidden" name="operation" value="manual"><input type="hidden" name="action" value="filter"><label for="query">Filter outputs</label><input :key="formKey('query', board.revision)" id="query" name="query" :value="board.query"><button type="submit" data-bench-action="filter">Filter</button></form>
              <form @submit="submit" novalidate><input type="hidden" name="session" :value="board.session"><input type="hidden" name="csrf" :value="csrf"><input type="hidden" name="operation" value="manual"><input type="hidden" name="action" value="save"><label for="title-input">Project name</label><input :key="formKey('title', board.revision)" id="title-input" name="title" :value="board.title_input"><button type="submit" data-bench-action="save">Save</button></form>
            </div>
            <p id="form-error" role="alert">{{ board.error }}</p><p id="form-notice" role="status">{{ board.notice }}</p>
            <div class="toolbar"><form v-for="action in [{name: 'insert', label: 'Insert output'}, {name: 'reorder', label: 'Reverse outputs'}, {name: 'remove', label: 'Remove inserted output'}, {name: 'probe', label: 'Check server'}]" :key="action.name" @submit="submit" novalidate><input type="hidden" name="session" :value="board.session"><input type="hidden" name="csrf" :value="csrf"><input type="hidden" name="operation" value="manual"><input type="hidden" name="action" :value="action.name"><button type="submit" :data-bench-action="action.name">{{ action.label }}</button></form></div>
          </section>
          <section id="project-tabs"><div role="tablist"><button v-for="tab in [{id: 'project-info', label: 'Project Info'}, ...board.note_tabs.map(group => ({id: group.id, label: group.title})), {id: 'outputs', label: 'Outputs'}]" :key="tab.id" type="button" role="tab" :data-tab-target="tab.id" :aria-controls="tab.id" :aria-selected="activeTab === tab.id" @click="activeTab = tab.id">{{ tab.label }}</button></div>
            <div id="project-info" role="tabpanel" data-tab-panel="project-info" :hidden="activeTab !== 'project-info'"><section class="project-info"><h2>Project Info</h2><table><tbody><tr><th scope="row">Org</th><td>{{ board.project.organization }}</td></tr><tr><th scope="row">Duration</th><td>{{ board.project.start_date }} – {{ board.project.end_date }}</td></tr><tr><th scope="row">Status</th><td>{{ board.project.status }}</td></tr><tr><th scope="row">Tags</th><td data-project-tags>{{ board.project_tags.length ? board.project_tags.join(', ') : 'No entries' }}</td></tr></tbody></table><section data-project-status-updates><h3>Status updates</h3><p v-if="!board.status_updates.length">No entries</p><ul v-else><li v-for="item in board.status_updates" :key="item.id" :data-status-update-id="item.id">{{ item.text }}</li></ul></section><section><h3>Team</h3><table><thead><tr><th>Name</th><th>Role</th></tr></thead><tbody><tr v-for="role in board.roles" :key="role.id" :data-role-id="role.id"><td class="user-name">{{ role.user_name }}</td><td class="role-name">{{ role.name }}</td></tr></tbody></table></section><section data-project-contacts><h3>Contacts</h3><p v-if="!board.contacts.length">No entries</p><ul v-else><li v-for="contact in board.contacts" :key="contact.id" :data-contact-id="contact.id">{{ contact.name }}</li></ul></section></section></div>
            <div v-for="group in board.note_tabs" :id="group.id" :key="group.id" role="tabpanel" :data-tab-panel="group.id" :hidden="activeTab !== group.id"><section class="project-notes"><h2>Notes</h2><article v-for="note in group.notes" :key="note.id" :data-note-id="note.id"><p class="note-text">{{ note.text }}</p><details><summary>Comments</summary><article v-for="comment in note.comments" :key="comment.id" :data-comment-id="comment.id"><p class="comment-text">{{ comment.text }}</p><small class="comment-author">{{ comment.author }}</small></article></details></article></section></div>
            <div id="outputs" role="tabpanel" data-tab-panel="outputs" :hidden="activeTab !== 'outputs'"><section id="rows" class="project-outputs"><h2>Outputs</h2><section v-for="phase in board.phase_groups" :id="`phase-${phase.id}`" :key="phase.id" :data-phase-id="phase.id" data-phase-expanded="true"><details open><summary><h3 class="phase-title">{{ phase.title }}</h3></summary><div><article v-for="output in phase.outputs" :id="output.element_id" :key="output.id" :data-row-id="output.id" :data-source-id="output.source_id ?? undefined" data-output-expanded="true" :data-selected="String(output.selected)">
<header>
<span class="row-title">{{ output.title }}</span>
<span class="row-status">{{ output.status }}</span>
<span :data-output-badge="output.completed ? 'done' : 'open'" class="output-badge">{{ output.dependencies.some(dependency => !dependency.completed) ? 'Missing dependency' : output.completed ? 'Completed' : 'In progress' }}</span>
</header>
<form class="output-form" @submit="submit" novalidate>
<input type="hidden" name="session" :value="board.session">
<input type="hidden" name="csrf" :value="csrf">
<input type="hidden" name="operation" value="manual">
<input type="hidden" name="action" value="select">
<input type="hidden" name="row_id" :value="output.id">
<label :for="`description-${output.id}`">Description</label>
<textarea :id="`description-${output.id}`" data-output-description>{{ output.description }}</textarea>
<label><input type="checkbox" data-output-completed :checked="output.completed"> Completed</label>
<button type="submit" :data-bench-action="`select-${output.id}`">Select</button>
</form>
<details open>
<summary>Output details</summary>
<section aria-label="Dependencies">
<h4>Dependencies</h4>
<article v-for="dependency in output.dependencies" :key="dependency.id" :data-dependency-id="dependency.id" :data-dependency-title="dependency.title" :data-dependency-completed="String(dependency.completed)">
<span aria-hidden="true">{{ dependency.completed ? '✓' : '⚠' }}</span> <span class="dependency-title">{{ dependency.title }}</span>
</article>
<p v-if="!output.dependencies.length">No dependencies</p>
</section>
<section class="output-attachments" aria-label="Attachments">
<h4>Attachments</h4>
<article v-for="attachment in output.attachments" :key="attachment.id" :data-attachment-id="attachment.id" :data-attachment-name="attachment.name">
<a class="attachment-name" :href="attachment.url">{{ attachment.name }}</a>
<ul class="attachment-tags"><li v-for="tag in attachment.tags" :key="tag" :data-attachment-tag="tag">{{ tag }}</li></ul>
</article>
<p v-if="!output.attachments.length">No attachments</p>
</section>
</details>
</article></div></details></section></section></div>
          </section>
        </main>
      </div>
    </section>
  </template>
</template>

<style>
[hidden] { display: none !important; }
</style>
