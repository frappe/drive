<template>
  <Dialog v-model="open" :options="{ title: 'Rename', size: 'xs' }">
    <template #body-content>
      <div class="flex items-center justify-center">
        <!-- Input field for new name -->
        <Input
          v-model="newName"
          class="w-full"
          type="text"
          @keyup.enter="submit"
        />
        
        <!-- File extension display (if any) -->
        <span
          v-if="entity.file_ext"
          :variant="'subtle'"
          theme="gray"
          size="sm"
          class="form-input font-medium ml-2 text-gray-700 border-gray-100"
        >
          {{ entity.file_ext.toUpperCase().slice(1) }}
        </span>
      </div>

      <!-- Inline error message (if any) -->
      <p v-if="errorMsg" class="text-sm text-red-600 mt-2">{{ errorMsg }}</p>

      <!-- Rename Button -->
      <div class="flex mt-8">
        <Button variant="solid" class="w-full" @click="submit" :disabled="isSubmitting">
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from "vue"
import { useToast } from "frappe-ui"
import { Dialog, Input, Button } from "frappe-ui"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { rename } from "@/resources/files"

const props = defineProps({ modelValue: String })
const emit = defineEmits(["update:modelValue", "success"])
const store = useStore()
const toast = useToast()

// Reactive states
const entity = computed(() => store.state.activeEntity)
const newName = ref("")
const ext = ref("")
const errorMsg = ref("") // For inline error message
const isSubmitting = ref(false) // To disable button during submission

// Initialize newName and ext based on entity data
if (entity.value.is_group || entity.value.document) {
  newName.value = entity.value.title
  if (useRoute().meta.documentPage) {
    store.state.activeEntity.title = newName.value
  }
} else {
  const parts = entity.value.title.split(".")
  if (parts.length > 1) {
    newName.value = parts.slice(0, -1).join(".").trim()
    ext.value = parts[parts.length - 1]
  } else {
    newName.value = parts[0]
  }
}

// Computed property to control Dialog open state
const open = computed({
  get: () => {
    return props.modelValue === "rn"
  },
  set: (value) => {
    emit("update:modelValue", value)
    if (!value) newName.value = ""
  },
})

// Submit function to rename the file
const submit = async () => {
  const new_title = newName.value + (ext.value ? "." + ext.value : "")

  // Prevent double submission
  if (isSubmitting.value) return

  try {
    isSubmitting.value = true // Disable the button during submission

    // Call backend validation
    await frappe.call("drive.files.validate_rename", {
      entity_name: entity.value.name,
      new_title,
    })

    // Emit success and rename the file
    emit("success", {
      name: entity.value.name,
      title: new_title,
    })

    rename.submit({
      entity_name: entity.value.name,
      new_title,
    })

    // Reset error message on success
    errorMsg.value = ""
  } catch (err) {
    // Show Toast notification for global feedback
    toast.show({
      title: "Rename Failed",
      description: err.message || "A file with that name already exists.",
      status: "error",
    })

    // Show inline error message
    errorMsg.value = err.message || "Rename failed. Please try another name."
  } finally {
    isSubmitting.value = false // Re-enable button after submission
  }
}
</script>

<style scoped>
/* Optional styling for error message */
.text-sm {
  font-size: 0.875rem;
}
.text-red-600 {
  color: #e53e3e;
}
.mt-2 {
  margin-top: 0.5rem;
}
</style>
