<template>
  <div
    v-if="isMobile"
    class="flex flex-col w-96 h-full justify-between grow"
  >
    <div class="grow flex items-center">
      <VuePDF
        class="border rounded-sm overflow-y-auto overflow-x-hidden max-h-[80vh]"
        :pdf
        :page
        fit-parent
        :text-layer="true"
      />
    </div>
    <div class="flex gap-2 justify-center items-center">
      <Button
        label="Prev"
        @click="page = page > 1 ? page - 1 : page"
      />

      <span class="text-sm">{{ page }} / {{ pages }}</span>
      <Button
        label="Next"
        @click="page = page < pages ? page + 1 : page"
      />
    </div>
  </div>
  <embed
    v-else
    ref="embed"
    :src
    type="application/pdf"
    class="w-full h-full max-h-[80vh] max-w-[80vw] self-center"
  />
</template>

<script setup>
import { computed, ref } from "vue"
import { breakpointsTailwind, useBreakpoints } from "@vueuse/core"
import { VuePDF, usePDF } from "@tato30/vue-pdf"
import "@tato30/vue-pdf/style.css"

const breakpoints = useBreakpoints(breakpointsTailwind)
const isMobile = breakpoints.smaller("sm")
const props = defineProps({
  previewEntity: Object,
})
const src = computed(
  () =>
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`
)

let page, pages, pdf
if (isMobile.value) {
  page = ref(3)
  ;({ pages, pdf } = usePDF(src.value))
}
</script>
