<template>
  <div>
    <ListView
      :entityName="entityName"
      :actionItems="actionItems"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
    />
    <FilePreview
      v-if="showPreview"
      @hide="hidePreview"
      :previewEntity="previewEntity"
    />
  </div>
</template>

<script>
import ListView from '@/components/ListView.vue'
import FilePreview from '@/components/FilePreview.vue'

export default {
  name: 'Home',
  components: {
    ListView,
    FilePreview,
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: '',
    },
  },
  data: () => ({
    showPreview: false,
    previewEntity: '',
    selectedEntities: [],
    actionItems: [],
  }),
  methods: {
    openEntity(entity) {
      if (entity.is_group) {
        this.$router.push({
          name: 'Folder',
          params: { entityName: entity.name },
        })
      } else {
        this.previewEntity = entity.name
        this.showPreview = true
      }
    },
    hidePreview() {
      this.showPreview = false
      this.previewEntity = ''
    },
  },
}
</script>
