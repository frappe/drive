<template>
  <Dialog
    v-model="open"
    :options="{ title: __('Rename'), size: 'xs' }"
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
      <div class="flex mt-4">
        <Button
          variant="solid"
          class="w-full !bg-[#0149C1] text-white hover:!opacity-90"
          @click="submit"
        >
          {{ __("Rename") }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { rename } from "@/resources/files"
import { Dialog, Input } from "frappe-ui"
import { computed, ref } from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"

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
