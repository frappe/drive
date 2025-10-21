<template>
  <div
    v-if="isMobile"
    class="flex flex-col gap-3 w-96 h-full justify-between grow"
  >
    <div class="flex gap-2 justify-center items-center">
      <Button
        @click="scale = scale > 0.25 ? scale - 0.25 : scale"
        :disabled="scale == 0.25"
        label="-"
      />
      <span class="text-sm">{{ scale * 100 }}%</span>
      <Button
        @click="scale = scale < 2 ? scale + 0.25 : scale"
        :disabled="scale == 2"
        label="+"
      />
    </div>
    <div class="grow flex items-center border rounded-sm max-h-[70vh]">
      <VuePDF
        class="rounded-sm overflow-y-auto overflow-x-auto w-full h-full"
        :pdf
        :page
        :scale
        :text-layer="true"
      >
        <LoadingIndicator class="w-10 text-neutral-100 mx-auto h-full" />
      </VuePDF>
    </div>
    <div
      v-if="pages"
      class="flex gap-2 justify-center items-center"
    >
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
import { LoadingIndicator } from "frappe-ui"
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

let page, pages, pdf, scale
if (isMobile.value) {
  page = ref(1)
  scale = ref(1)
  ;({ pages, pdf } = usePDF(src.value))
}
</script>
