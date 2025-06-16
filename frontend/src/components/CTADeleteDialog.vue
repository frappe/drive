<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Are you sure?', size: 'sm' }"
  >
    <template #body-content>
      <p class="text-ink-gray-5">
        {{ current.message }}
      </p>
      <div class="flex mt-5">
        <Button
          :variant="current.buttonVariant"
          theme="red"
          icon-left="trash-2"
          class="w-full"
          :loading="current.resource.loading"
          @click="current.resource.submit(null) && emit('success')"
        >
          {{ current.buttonText }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { Dialog } from "frappe-ui"
import { computed } from "vue"
import { useRoute } from "vue-router"
import { toggleFav, clearRecent, clearTrash } from "@/resources/files"

const props = defineProps({
  modelValue: String,
  entities: Array,
})
const emit = defineEmits(["update:modelValue", "success"])

const open = computed({
  get: () => {
    return props.modelValue === "cta"
  },
  set: (value) => {
    emit("update:modelValue", value)
  },
})

document.onkeydown = (e) => {
  if (e.key === "Escape") open.value = false
}

const route = useRoute()
const dialogConfigs = [
  {
    route: "Recents",
    message: "All your recently viewed files will be cleared.",
    buttonText: "Clear",
    resource: clearRecent,
  },
  {
    route: "Favourites",
    message: "All your favourite items will be cleared.",
    buttonText: "Clear",
    resource: toggleFav,
  },
  {
    route: "Trash",
    message:
      "All items in your Trash will be deleted forever. This is an irreversible process.",
    buttonVariant: "solid",
    buttonText: "Delete",
    resource: clearTrash,
  },
]
const current = dialogConfigs.find(({ route: _route }) => _route === route.name)
</script>
