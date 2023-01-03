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
    old_colors() {
      return ['#FF6633', '#FFB399', '#FF33FF', '#FFFF99', '#00B3E6',
        '#E6B333', '#3366E6', '#999966', '#99FF99', '#B34D4D',
        '#80B300', '#809900', '#E6B3B3', '#6680B3', '#66991A',
        '#FF99E6', '#CCFF1A', '#FF1A66', '#E6331A', '#33FFCC',
        '#66994D', '#B366CC', '#4D8000', '#B33300', '#CC80CC',
        '#66664D', '#991AFF', '#E666FF', '#4DB3FF', '#1AB399',
        '#E666B3', '#33991A', '#CC9999', '#B3B31A', '#00E680',
        '#4D8066', '#809980', '#E6FF80', '#1AFF33', '#999933',
        '#FF3380', '#CCCC00', '#66E64D', '#4D80CC', '#9900B3',
        '#E64D66', '#4DB380', '#FF4D4D', '#99E6E6', '#6666FF'];
    },
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
      console.log(colors) 
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
        v
      },
    },
  },
  resources: {
    updateColor() {
      return {
        method: 'drive.api.files.call_controller_method',
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
          console.log(this.newColor)
          console.log(data)
          this.$emit('success', data)
        },
      }
    },
  }
}
</script>