<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Rename', size: 'xs' }"
  >
    <template #body-content>
      <div class="flex items-center justify-center">
        <Input
          v-model="newName"
          v-focus
          class="w-full"
          type="text"
          @keyup.enter="submit"
        />
        <span
          v-if="entity.file_ext"
          :variant="'subtle'"
          theme="gray"
          size="sm"
          class="form-input font-medium ml-2 text-ink-gray-7 border-gray-100"
        >
          {{ entity.file_ext.toUpperCase().slice(1) }}
        </span>
      </div>
      <div class="flex mt-8">
        <Button
          variant="solid"
          class="w-full"
          @click="submit"
        >
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from "vue"
import { Dialog, Input } from "frappe-ui"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { rename } from "@/resources/files"

const props = defineProps({ entity: Object, modelValue: String })
const emit = defineEmits(["update:modelValue", "success"])
const store = useStore()

const newName = ref("")
const ext = ref("")

if (props.entity.is_group || props.entity.document) {
  newName.value = props.entity.title
  if (useRoute().meta.documentPage) {
    store.state.activeEntity.title = newName.value
  }
} else {
  const parts = props.entity.title.split(".")
  if (parts.length > 1) {
    newName.value = parts.slice(0, -1).join(".").trim()
    ext.value = parts[parts.length - 1]
  } else {
    newName.value = parts[0]
  }
}

const open = computed({
  get: () => {
    return props.modelValue === "rn"
  },
  set: (value) => {
    emit("update:modelValue", value || "")
    if (!value) newName.value = ""
  },
})

const submit = () => {
  rename.submit({
    entity_name: props.entity.name,
    new_title: newName.value + (ext.value ? "." + ext.value : ""),
  })
  emit("success", {
    name: props.entity.name,
    title: newName.value + (ext.value ? "." + ext.value : ""),
  })
}
</script>
