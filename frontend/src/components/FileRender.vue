<template>
    <Spinner v-if="preview.loading" class="w-10 h-10 z-10 text-neutral-100 mx-auto" />
    <div v-else-if="preview.error "
        class="p-8 z-10 bg-[#252728] rounded-md text-neutral-100 text-xl text-center font-medium">
        {{ preview.error }}
    </div>
    <img v-else-if="isImage" :src="preview.url" class="object-contain max-h-[95vh] max-w-[80vw] z-10" />
    <div v-else class="max-h-[95vh] max-w-[80vw] z-10 bg-[#252728] rounded-lg shadow-xl">
        <iframe class="w-full h-[90vh]" :src="preview.url" />
    </div>
</template>

<script>
import { Spinner } from 'frappe-ui'
export default {
    name: 'FileRender',
    components: {
        Spinner,
    },
    props: {
        previewEntity: {
            type: Object,
            required: true,
        },
    },
    data() {
        return {
            preview: {
                loading: true,
                error: null,
                url: '',
            },
            isImage: this.previewEntity.mime_type?.startsWith('image/'),
        }
    },
    mounted() {
        this.renderContent()
    },
    watch: {
        previewEntity() {
            this.renderContent()
        },
    },
    methods: {
        renderContent() {
            const isSupportedType =
                this.previewEntity.mime_type &&
                ['image', 'video', 'application/pdf'].some((type) =>
                    this.previewEntity.mime_type.startsWith(type)
                )
            if (!isSupportedType) {
                this.preview.error = 'Previews are not supported for this file type'
                this.preview.loading = false
            } else if (this.previewEntity.size_in_bytes > 100 * 1024 * 1024) {
                // Size limit = 100MB
                this.preview.error = 'File is too large to preview'
                this.preview.loading = false
            } else {
                this.fetchContent()
            }
        },
        async fetchContent() {
            const headers = {
                Accept: 'application/json',
                'Content-Type': 'application/json; charset=utf-8',
                'X-Frappe-Site-Name': window.location.hostname,
            }
            const res = await fetch(
                `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`,
                {
                    method: 'GET',
                    headers,
                }
            )
            if (res.ok) {
                const blob = await res.blob()
                this.preview.url = URL.createObjectURL(blob)
                this.preview.loading = false
            } else {
                this.preview.error = 'No preview available'
                this.preview.loading = false
            }
        },
    },
}
</script>