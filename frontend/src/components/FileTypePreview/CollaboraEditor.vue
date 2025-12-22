<template>
  <div class="collabora-editor-container w-full h-full">
    <!-- Hidden form to POST the access token to Collabora -->
    <form
      ref="collaboraForm"
      :action="editorUrl"
      method="POST"
      target="collabora-frame"
      class="hidden"
    >
      <input type="hidden" name="access_token" :value="accessToken" />
    </form>

    <!-- Collabora iframe -->
    <iframe
      v-if="editorUrl && accessToken"
      ref="collaboraFrame"
      name="collabora-frame"
      class="w-full h-full border-0"
      :title="fileName"
      allow="clipboard-read; clipboard-write"
      allowfullscreen
    ></iframe>

    <!-- Loading state -->
    <div
      v-else
      class="flex items-center justify-center h-full"
    >
      <div class="text-center">
        <LucideLoader2 class="size-8 animate-spin mx-auto mb-4 text-ink-gray-5" />
        <span class="text-ink-gray-7">{{ __("Loading editor...") }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue"
import { createResource } from "frappe-ui"

const props = defineProps({
  fileId: {
    type: String,
    required: true,
  },
  fileName: {
    type: String,
    default: "Document",
  },
})

const emit = defineEmits(["close", "saved"])

const editorUrl = ref(null)
const accessToken = ref(null)
const collaboraForm = ref(null)
const collaboraFrame = ref(null)

// Resource to get editor configuration
const editorConfig = createResource({
  url: "drive_wopi.wopi.discovery.get_editor_config",
  makeParams() {
    return { file_id: props.fileId }
  },
  onSuccess(data) {
    if (data.editor_url && data.access_token) {
      editorUrl.value = data.editor_url
      accessToken.value = data.access_token

      // Submit the form after setting values
      nextTick(() => {
        if (collaboraForm.value) {
          collaboraForm.value.submit()
        }
      })
    }
  },
  onError(error) {
    console.error("Failed to get editor config:", error)
  },
})

// Handle PostMessage from Collabora
function handlePostMessage(event) {
  // Verify origin if needed
  const data = event.data

  if (typeof data === "string") {
    try {
      const parsed = JSON.parse(data)
      handleCollaboraMessage(parsed)
    } catch (e) {
      // Not JSON, ignore
    }
  } else if (typeof data === "object") {
    handleCollaboraMessage(data)
  }
}

function handleCollaboraMessage(message) {
  const messageId = message.MessageId || message.message_id

  switch (messageId) {
    case "UI_Close":
    case "close":
      emit("close")
      break
    case "Doc_ModifiedStatus":
      // Document modification status changed
      if (message.Values && message.Values.Modified === false) {
        emit("saved")
      }
      break
    case "Action_Save_Resp":
      // Save response
      if (message.Values && message.Values.success) {
        emit("saved")
      }
      break
  }
}

onMounted(() => {
  // Load editor configuration
  editorConfig.fetch()

  // Listen for PostMessage from Collabora
  window.addEventListener("message", handlePostMessage)
})

onUnmounted(() => {
  window.removeEventListener("message", handlePostMessage)
})

// Watch for fileId changes
watch(
  () => props.fileId,
  () => {
    editorConfig.fetch()
  }
)
</script>

<style scoped>
.collabora-editor-container {
  min-height: 500px;
}
</style>
