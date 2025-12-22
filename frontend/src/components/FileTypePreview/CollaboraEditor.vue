<template>
  <div class="collabora-editor-container">
    <!-- Hidden form to submit token via POST -->
    <form
      ref="wopiForm"
      :action="editorUrl"
      method="POST"
      target="collabora-frame"
      class="hidden"
    >
      <input type="hidden" name="access_token" :value="accessToken" />
      <input type="hidden" name="access_token_ttl" :value="accessTokenTtl" />
    </form>

    <!-- Loading state -->
    <div v-if="loading" class="loading-container">
      <div class="loading-content">
        <div class="spinner"></div>
        <p class="loading-text">{{ __('Loading editor...') }}</p>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-container">
      <div class="error-content">
        <p class="error-title">{{ __('Loading error') }}</p>
        <p class="error-message">{{ error }}</p>
        <button @click="loadEditor" class="retry-button">
          {{ __('Retry') }}
        </button>
      </div>
    </div>

    <!-- Editor iframe -->
    <iframe
      v-show="!loading && !error"
      ref="editorFrame"
      name="collabora-frame"
      class="editor-frame"
      :title="fileName"
      sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
      allow="clipboard-read; clipboard-write"
      @load="onFrameLoad"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  fileId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'save', 'error', 'loaded'])

// State
const loading = ref(true)
const error = ref(null)
const editorUrl = ref('')
const accessToken = ref('')
const accessTokenTtl = ref(0)
const fileName = ref('')

// Refs
const wopiForm = ref(null)
const editorFrame = ref(null)

// Translation helper
const __ = (text) => {
  if (window.__ && typeof window.__ === 'function') {
    return window.__(text)
  }
  return text
}

// API Resource
const editorConfigResource = createResource({
  url: 'drive_wopi.wopi.discovery.get_editor_config',
  onSuccess(data) {
    editorUrl.value = data.editor_url
    accessToken.value = data.access_token
    accessTokenTtl.value = data.access_token_ttl
    fileName.value = data.file_name

    // Submit form after next render
    nextTick(() => {
      if (wopiForm.value) {
        wopiForm.value.submit()
      }
    })
  },
  onError(err) {
    error.value = err.message || __('Unable to load editor')
    loading.value = false
    emit('error', err)
  }
})

// Load editor
async function loadEditor() {
  loading.value = true
  error.value = null

  await editorConfigResource.submit({
    file_id: props.fileId
  })
}

// Handle iframe load
function onFrameLoad() {
  loading.value = false
  emit('loaded')
}

// Handle PostMessage from Collabora
function handlePostMessage(event) {
  const data = event.data

  if (typeof data === 'object' && data.MessageId) {
    switch (data.MessageId) {
      case 'UI_Close':
        emit('close')
        break
      case 'Action_Save':
      case 'Doc_ModifiedStatus':
        if (data.Values?.Modified === false) {
          emit('save')
        }
        break
      case 'App_LoadingStatus':
        if (data.Values?.Status === 'Document_Loaded') {
          loading.value = false
          emit('loaded')
        }
        break
    }
  }
}

// Send command to Collabora
function sendCommand(command) {
  if (editorFrame.value && editorFrame.value.contentWindow) {
    editorFrame.value.contentWindow.postMessage(
      JSON.stringify(command),
      '*'
    )
  }
}

// Force save
function save() {
  sendCommand({
    MessageId: 'Action_Save',
    Values: { DontTerminateEdit: true }
  })
}

// Lifecycle
onMounted(() => {
  window.addEventListener('message', handlePostMessage)
  loadEditor()
})

onUnmounted(() => {
  window.removeEventListener('message', handlePostMessage)
})

// Expose methods to parent
defineExpose({
  reload: loadEditor,
  save
})
</script>

<style scoped>
.collabora-editor-container {
  width: 100%;
  height: 100%;
  min-height: 600px;
  position: relative;
  background-color: #f5f5f5;
}

.hidden {
  display: none;
}

.loading-container,
.error-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.loading-content,
.error-content {
  text-align: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #6b7280;
  font-size: 14px;
}

.error-title {
  color: #dc2626;
  font-weight: 500;
  margin-bottom: 4px;
}

.error-message {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 12px;
}

.retry-button {
  padding: 8px 16px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background-color: #2563eb;
}

.editor-frame {
  width: 100%;
  height: 100%;
  border: none;
  min-height: 600px;
}
</style>
