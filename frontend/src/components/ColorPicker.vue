<template>
  <Dialog :options="{ title: 'Change Color', size: 'xl', }" v-model="open">
    <template #body-content>
      <button @click="$resources.updateColor.submit({
      method: 'change_color',
      entity_name: this.entityName,
      new_color: color
      })" :value="entity?.color" class="mx-3 my-1 h-7 w-7 rounded-md" :style="{ backgroundColor: color }"
        v-for="color in colors" :key="color" />
    </template>
  </Dialog>
</template>
<script>
import { Dialog, Input, ErrorMessage } from 'frappe-ui'
import { theme } from '@/utils/theme'

export default {
  name: 'ColorPicker',
  components: {
    Dialog,
    Input,
    ErrorMessage,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    entity: {
      type: Object,
      required: true,
    },
  },
  emits: ['update:modelValue', 'success'],
  data() {
    return {
      newColor: '',
      errorMessage: '',
    }
  },
  methods: {
    getColors(name) {
      return Object.keys(theme.colors[name]).map((key) => theme.colors[name][key])
    },
    getAllColors() {
      return {
        gray: this.getColors('gray'),
        red: this.getColors('red'),
        orange: this.getColors('orange'),
        yellow: this.getColors('yellow'),
        green: this.getColors('green'),
        blue: this.getColors('blue'),
        purple: this.getColors('purple'),
        pink: this.getColors('pink'),
      }
    },
  },
  computed: {
    colors() {
      let colors = this.getAllColors()
      return [
        ...colors.gray,
        ...colors.red,
        ...colors.orange,
        ...colors.yellow,
        ...colors.green,
        ...colors.blue,
        ...colors.purple,
        ...colors.pink,
      ]
    },
    entityName() {
      return this.entity?.name
    },
    entityColor() {
      return this.entity?.color
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
        if (!value) {
          this.newColor = ''
          this.errorMessage = ''
        }
      },
    },
  },
  resources: {
    updateColor() {
      return {
        url: 'drive.api.files.call_controller_method',
        params: {
          method: 'change_color',
          entity_name: this.entityName,
          new_color: this.newColor,
        },
        validate(params) {
          if (!params?.new_color) {
            return 'New name is required'
          }
        },
        onSuccess(data) {
          this.newColor = ''
          this.$emit('success', data)
        },
      }
    },
  }
}
</script>