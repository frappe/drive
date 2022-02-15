<template>
  <ListView :entityName="entityName" />
</template>

<script>
import ListView from '@/components/ListView.vue'

export default {
  name: 'Home',
  components: {
    ListView,
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: '',
    },
  },
}
</script>
