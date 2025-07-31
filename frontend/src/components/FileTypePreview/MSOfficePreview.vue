<template>
  <div class="w-full h-full">
    <iframe
      v-if="officeUrl"
      :src="officeUrl"
      width="100%"
      height="100%"
      frameborder="0"
    ></iframe>
    <div v-else class="text-center mt-10 text-gray-500">
      Đang tải bản xem trước...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const officeUrl = ref('')
const route = useRoute()

onMounted(async () => {
  const fileId = route.params.entityName as string
  console.log('fileId:', route.params)
  if (!fileId) {
    console.warn('Không có entityName trong route params.')
    return
  }

  try {
    const res = await fetch(`/api/method/drive.api.files.get_file_signed_url?docname=${fileId}`)
    const data = await res.json()

    const signed_url = data?.message?.signed_url
    if (signed_url) {
      const encoded = encodeURIComponent(signed_url)
      officeUrl.value = `https://view.officeapps.live.com/op/view.aspx?src=${encoded}`
    } else {
      console.error('Không nhận được signed_url hợp lệ:', data)
    }
  } catch (error) {
    console.error('Lỗi khi gọi API lấy signed_url:', error)
  }
})
</script>

<style scoped>
iframe {
  border: none;
  min-height: 600px;
}
</style>
