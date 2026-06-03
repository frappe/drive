<template>
  <div class="drive-picker">
    <!-- Tabs: Site (framework files) / Home (personal Drive) / Teams -->
    <div class="tab-bar">
      <button v-for="t in tabs" :key="t.key" class="tab" :class="{ active: tab === t.key }" @click="switchTab(t.key)">
        <span class="tab-icon" v-html="t.icon" />
        {{ t.label }}
      </button>
    </div>

    <!-- Team selector (Teams tab only) -->
    <select v-if="tab === 'teams'" class="team-select" :value="team" @change="selectTeam($event.target.value)">
      <option value="" disabled>{{ __('Select a team') }}</option>
      <option v-for="t in teams" :key="t.name" :value="t.name">
        {{ t.title }}
      </option>
    </select>

    <!-- Search -->
    <input v-model="searchText" type="search" class="search" :placeholder="tab === 'site' ? __('Search site files') : __('Search this team')
      " />

    <!-- Breadcrumbs (hidden while searching) -->
    <div v-if="!searching" class="crumbs">
      <template v-for="(c, i) in crumbs" :key="c.name">
        <button class="crumb" :class="{ last: i === crumbs.length - 1 }" @click="goTo(i)">
          {{ c.label }}
        </button>
        <span v-if="i < crumbs.length - 1" class="crumb-sep">/</span>
      </template>
    </div>
    <div v-else class="crumbs">
      <span class="crumb last">{{ __('Search results') }}</span>
    </div>

    <!-- List -->
    <div ref="listEl" class="list" @scroll="onScroll">
      <div v-if="loading" class="state">
        <span class="spinner-border spinner-border-sm" />
      </div>
      <div v-else-if="!rows.length" class="state muted">
        {{ searching ? __('No matches') : __('Empty folder') }}
      </div>
      <button v-for="row in rows" :key="row.name" class="file-row"
        :class="{ selected: selected && selected.name === row.name }" @click="onRow(row)"
        @dblclick="row.is_folder && openFolder(row)">
        <img class="row-icon" :src="iconUrl(row)" @error="$event.target.src = UNKNOWN_ICON" />
        <span class="row-name" :title="row.file_name">{{ row.file_name }}</span>
        <span v-if="row.is_folder" class="row-chevron" v-html="chevronIcon" />
      </button>
      <div v-if="loadingMore" class="state">
        <span class="spinner-border spinner-border-sm" />
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="footer-info">
        <template v-if="staged">
          {{ __('Upload') }} <b>{{ staged.name }}</b> {{ __('to') }}
          <b>{{ here.label }}</b>
        </template>
        <template v-else-if="selected">
          {{ __('Attach') }} <b>{{ selected.file_name }}</b>
        </template>
        <template v-else-if="canUpload">
          {{ __('Choose a file, or open a folder') }}
        </template>
        <template v-else>{{ __('Choose a file to attach') }}</template>
      </div>

      <input ref="fileInput" type="file" class="hidden" @change="onStage" />
      <button v-if="canUpload" class="ghost-btn" @click="$refs.fileInput.click()">
        {{ __('Upload new…') }}
      </button>
      <button class="primary-btn" :disabled="!ready || busy" @click="submit">
        <span v-if="busy" class="spinner-border spinner-border-sm" />
        <template v-else>{{ staged ? __('Upload & attach') : __('Attach') }}</template>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const chevronIcon =
  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>'

const props = defineProps({
  uploader: { type: Object, required: true },
  onComplete: { type: Function, default: () => { } },
})

const tabs = [
  { key: 'site', label: __('Site'), icon: frappe.utils.icon('globe', 'sm') },
  { key: 'home', label: __('Home'), icon: frappe.utils.icon('home', 'sm') },
  { key: 'teams', label: __('Teams'), icon: frappe.utils.icon('users', 'sm') },
]

const tab = ref('home')
const rows = ref([])
const loading = ref(false) // initial page
const loadingMore = ref(false) // appending next page
const selected = ref(null)
const staged = ref(null)
const busy = ref(false)
const fileInput = ref(null)
const listEl = ref(null)

const teams = ref([])
const team = ref('')
let personalTeam = ''

const PAGE = 50
const start = ref(0)
const hasMore = ref(false)
const searchText = ref('')
const searching = computed(() => searchText.value.trim().length >= 2)

// Breadcrumb trail for the active tab. The tip is the current folder, which is
// also the upload destination on the Drive tabs.
const crumbs = ref([{ name: '', label: __('Home') }])
const here = computed(() => crumbs.value[crumbs.value.length - 1])
const canUpload = computed(() => tab.value !== 'site')
const ready = computed(() => (staged.value ? canUpload.value : !!selected.value))

onMounted(async () => {
  const { message } = await frappe.call('drive.api.permissions.get_teams', { details: 1 })
  teams.value = Object.values(message || {})
  const dt = await frappe.call('drive.utils.get_default_team')
  personalTeam = dt.message || ''
  team.value = teams.value[0]?.name || ''
  switchTab('home')
})

function rootCrumb(key) {
  if (key === 'site') return { name: 'Home', label: __('Site') }
  if (key === 'home') return { name: '', label: __('Home') }
  const t = teams.value.find((x) => x.name === team.value)
  return { name: '', label: t ? t.title : __('Team') }
}

function switchTab(key) {
  tab.value = key
  searchText.value = ''
  selected.value = null
  staged.value = null
  crumbs.value = [rootCrumb(key)]
  reload()
}

function selectTeam(name) {
  team.value = name
  searchText.value = ''
  selected.value = null
  staged.value = null
  crumbs.value = [rootCrumb('teams')]
  reload()
}

function openFolder(row) {
  searchText.value = ''
  selected.value = null
  crumbs.value.push({ name: row.name, label: row.file_name })
  reload()
}

function goTo(i) {
  if (i === crumbs.value.length - 1) return
  selected.value = null
  crumbs.value = crumbs.value.slice(0, i + 1)
  reload()
}

function onRow(row) {
  if (row.is_folder) return openFolder(row)
  selected.value = row
  staged.value = null
}

function onStage(e) {
  staged.value = e.target.files[0] || null
  selected.value = null
}

// Re-fetch from the first page (tab/folder change or a new search).
async function reload() {
  start.value = 0
  rows.value = []
  loading.value = true
  try {
    const { items, more } = await fetchPage(0)
    rows.value = sortRows(items)
    hasMore.value = more
    start.value = items.length
  } finally {
    loading.value = false
  }
  topUp()
}

async function loadMore() {
  if (loadingMore.value || loading.value || !hasMore.value) return
  loadingMore.value = true
  try {
    const { items, more } = await fetchPage(start.value)
    rows.value = rows.value.concat(sortRows(items))
    hasMore.value = more
    start.value += items.length
  } finally {
    loadingMore.value = false
  }
}

function onScroll(e) {
  const el = e.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 60) loadMore()
}

// A short first page may not fill the scroll area; keep topping up.
function topUp() {
  requestAnimationFrame(() => {
    const el = listEl.value
    if (el && hasMore.value && el.scrollHeight <= el.clientHeight) loadMore()
  })
}

const sortRows = (items) =>
  items.slice().sort((a, b) => Number(b.is_folder) - Number(a.is_folder))

// One page of results: { items, more }. Source depends on the tab + search mode.
async function fetchPage(offset) {
  const q = searchText.value.trim()
  if (tab.value === 'site') {
    if (q) {
      // Framework's global file search (not paged); only fetch once.
      if (offset > 0) return { items: [], more: false }
      const r = await frappe.call('frappe.core.api.file.get_files_by_search_text', { text: q })
      return { items: r.message || [], more: false }
    }
    const r = await frappe.call('frappe.core.api.file.get_files_in_folder', {
      folder: here.value.name || 'Home',
      start: offset,
      page_length: PAGE,
    })
    return { items: r.message?.files || [], more: !!r.message?.has_more }
  }
  // Drive tabs (Home / Teams). With a query, list.files searches the whole team.
  const t = tab.value === 'home' ? personalTeam : team.value
  if (!t) return { items: [], more: false }
  const r = await frappe.call('drive.api.list.files', {
    team: t,
    entity_name: here.value.name,
    search: q || undefined,
    start: offset,
    limit: PAGE,
  })
  const raw = r.message || []
  return { items: raw.filter((f) => !f.file_name?.startsWith('.')), more: raw.length === PAGE }
}

let searchTimer = null
watch(searchText, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reload, 300)
})

// ---- file-type icons (matches Drive's list view) ----
const ICON_BASE = '/assets/drive/images/icons'
const UNKNOWN_ICON = `${ICON_BASE}/unknown.svg`

// Maps a file extension to one of Drive's icon names for framework (Site) rows,
// which don't carry a Drive `file_type`.
const EXT_ICON = {
  pdf: 'pdf',
  png: 'image', jpg: 'image', jpeg: 'image', gif: 'image', webp: 'image', svg: 'image', heic: 'image', bmp: 'image',
  mp4: 'video', mov: 'video', webm: 'video', mkv: 'video', avi: 'video',
  mp3: 'audio', wav: 'audio', m4a: 'audio', flac: 'audio',
  zip: 'archive', tar: 'archive', gz: 'archive', rar: 'archive', '7z': 'archive',
  doc: 'word', docx: 'word',
  xls: 'excel', xlsx: 'excel', csv: 'spreadsheet',
  ppt: 'presentation', pptx: 'presentation',
  md: 'markdown', txt: 'text',
  py: 'code', js: 'code', ts: 'code', json: 'code', html: 'code', css: 'code', vue: 'code',
}

function iconUrl(row) {
  if (row.is_folder) return `${ICON_BASE}/folder.svg`
  if (row.file_type) return `${ICON_BASE}/${row.file_type.toLowerCase()}.svg`
  const ext = (row.file_name || '').split('.').pop().toLowerCase()
  return `${ICON_BASE}/${EXT_ICON[ext] || 'unknown'}.svg`
}

// ---- actions ----
async function submit() {
  busy.value = true
  try {
    if (staged.value) {
      const t = tab.value === 'home' ? personalTeam : team.value
      const driveFile = await driveUpload(staged.value, t, here.value.name)
      attach(driveFile.name)
    } else {
      attach(selected.value.name)
    }
    props.onComplete()
  } catch (err) {
    frappe.msgprint({
      title: __('Upload failed'),
      message: err.message,
      indicator: 'red',
    })
  } finally {
    busy.value = false
  }
}

// Hand the file to the framework engine via library_file_name so the caller's
// on_success (field + attachments) fires exactly as before.
function attach(libraryFileName) {
  props.uploader.upload_file({ library_file_name: libraryFileName })
}

async function driveUpload(file, t, parent) {
  const form = new FormData()
  form.append('file', file, file.name)
  form.append('team', t)
  if (parent) form.append('parent', parent)
  form.append('total_file_size', file.size)
  form.append('uuid', frappe.utils.get_random(10))
  const res = await fetch('/api/method/drive.api.files.upload_file', {
    method: 'POST',
    headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
    body: form,
  })
  const data = await res.json()
  if (!res.ok) {
    const msgs = JSON.parse(data?._server_messages || '[]')
    throw new Error(
      msgs.length ? JSON.parse(msgs[0]).message : __('Could not upload to Drive')
    )
  }
  return data.message
}

defineExpose({ submit })
</script>

<style scoped>
.drive-picker {
  display: flex;
  flex-direction: column;
  font-size: var(--text-base);
  color: var(--ink-gray-8);
}

/* Tabs */
.tab-bar {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--outline-gray-1, #e5e5e5);
}

.tab {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  border-bottom: 1.5px solid transparent;
  padding: 0.5rem 0.25rem;
  margin-right: 0.75rem;
  font-size: var(--text-sm);
  color: var(--ink-gray-5);
  cursor: pointer;
}

.tab.active {
  color: var(--ink-gray-9);
  border-bottom-color: var(--ink-gray-9);
  font-weight: 500;
}

.tab-icon {
  display: inline-flex;
  width: 14px;
  height: 14px;
}

/* Team select */
.team-select {
  margin-top: 0.75rem;
  font-size: var(--text-sm);
  height: 1.75rem;
  border: 1px solid var(--outline-gray-2, #e0e0e0);
  border-radius: var(--border-radius, 8px);
  background: var(--surface-gray-2);
  padding: 0 0.5rem;
}

/* Search */
.search {
  margin-top: 0.75rem;
  font-size: var(--text-sm);
  height: 1.85rem;
  border: 1px solid var(--outline-gray-2, #e0e0e0);
  border-radius: var(--border-radius, 8px);
  background: var(--surface-gray-2);
  padding: 0 0.6rem;
  width: 100%;
}

.search:focus {
  outline: none;
  background: var(--surface-white, #fff);
  border-color: var(--outline-gray-3, #b3b3b3);
}

/* Breadcrumbs */
.crumbs {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  overflow: hidden;
  gap: 0.15rem;
  padding: 0.6rem 0 0.4rem;
}

.crumb {
  background: none;
  border: none;
  padding: 0.1rem 0.3rem;
  border-radius: 6px;
  font-size: var(--text-sm);
  color: var(--ink-gray-5);
  cursor: pointer;
  white-space: nowrap;
  max-width: 10rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.crumb:hover {
  background: var(--surface-gray-2);
}

.crumb.last {
  color: var(--ink-gray-8);
  font-weight: 500;
}

.crumb-sep {
  color: var(--ink-gray-4, #c4c4c4);
  font-size: var(--text-sm);
}

/* List */
.list {
  height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.state {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
}

.muted {
  color: var(--ink-gray-5);
  font-size: var(--text-sm);
}

.file-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  margin: 0;
  padding: 0.4rem 0.5rem;
  border-radius: var(--border-radius, 8px);
  cursor: pointer;
  color: var(--ink-gray-8);
}

.file-row:hover {
  background: var(--surface-gray-2);
}

.file-row.selected {
  background: var(--surface-gray-3);
}

.row-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  object-fit: contain;
}

.row-name {
  flex: 1;
  font-size: var(--text-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-chevron {
  width: 14px;
  height: 14px;
  color: var(--ink-gray-4, #c4c4c4);
  flex-shrink: 0;
  display: inline-flex;
}

/* Footer */
.footer {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-top: 1px solid var(--outline-gray-1, #e5e5e5);
  padding-top: 0.75rem;
  margin-top: 0.25rem;
}

.footer-info {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--ink-gray-5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer-info b {
  color: var(--ink-gray-8);
  font-weight: 500;
}

.hidden {
  display: none;
}

.ghost-btn,
.primary-btn {
  font-size: var(--text-sm);
  height: 1.75rem;
  padding: 0 0.75rem;
  border-radius: var(--border-radius, 8px);
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.ghost-btn {
  background: var(--surface-gray-2);
  color: var(--ink-gray-8);
}

.ghost-btn:hover {
  background: var(--surface-gray-3);
}

.primary-btn {
  background: var(--surface-gray-7, #383838);
  color: var(--ink-white, #fff);
}

.primary-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
