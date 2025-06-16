<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Delete Forever?', size: 'sm' }"
  >
    <template #body-content>
      <p class="text-ink-gray-5">
        {{ entities.length === 1 ? `This item` : `${entities.length} items` }}
        will be deleted forever. This is an irreversible process.
      </p>
      <div class="flex mt-5">
        <Button
          variant="solid"
          theme="red"
          icon-left="trash-2"
          class="w-full"
          :loading="deleteEntities.loading"
          @click="deleteEntities.submit()"
        >
          Delete — forever.
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { createResource, Dialog } from "frappe-ui"
import { del } from "idb-keyval"
import { computed } from "vue"

const emit = defineEmits(["update:modelValue", "success"])
const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  entities: {
    type: Object,
    required: false,
    default: null,
  },
})

const open = computed({
  get() {
    return props.modelValue === "d"
  },
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})

const deleteEntities = createResource({
  url: "drive.api.files.delete_entities",
  params: {
    entity_names: JSON.stringify(props.entities?.map((entity) => entity.name)),
  },
  onSuccess(data) {
    props.entities.map((entity) => del(entity.name))
    emit("success", data)
  },
})
</script>
