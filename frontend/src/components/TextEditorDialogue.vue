<template>
  <Dialog :options="{
    size: '7xl', actions: [
      { label: 'Save', appearance: 'primary', },
      { label: 'Discard' },
    ],
  }" v-model="open">
    <template #body-title>
      <input class="border-0 bg-white px-2 py-2 text-3xl font-normal focus:outline-0" placeholder="Untitled File" />
    </template>
    <template #body-content>
      <TextEditor editor-class="h-[75vh] prose-lg border max-w-none rounded-b-lg p-3 overflow-auto focus:outline-none"
        :fixedMenu="true" :content="content" @change="(val) => (content = val)" />
    </template>
    <div class="flex mt-8">
      <Button @click="open = false" class="ml-auto"> Cancel </Button>
      <Button appearance="primary" class="ml-4" @click="$resources.rename.submit()"
        :loading="$resources.rename.loading">
        Rename
      </Button>
    </div>
  </Dialog>
</template>

<script>
import { Input, Dialog, TextEditor, Button } from 'frappe-ui'

export default {
  name: 'ColorPicker',
  components: {
    Input,
    TextEditor,
    Dialog,
    Button,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['update:modelValue', 'success'],
  data() {
    return {
     content: "",
     inputClass: "prose-xl bg-black",
    }
  },
  computed: {
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
        
      },
    },
  },
}

</script>
