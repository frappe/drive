<template>
    <div class="w-96 flex flex-col">
        <div v-if="$store.state.showInfo" class="mx-5 mb-3">
            <div class="my-4">
                <FeatherIcon name="x" class="h-4 cursor-pointer" @click="$store.commit('setShowInfo', false)" />
            </div>
            <div>
                <div class="font-semibold">{{entity.title}}</div>
            </div>
        </div>
        <div class="h-11 flex cursor-pointer text-base">
            <div class="w-1/2 flex border-b" :class="{ 'text-gray-500': tab, 'border-blue-500': !tab }" @click="tab=0">
                <div class="m-auto">Detail</div>
            </div>
            <div class="w-1/2 flex border-b" :class="{ 'text-gray-500': !tab, 'border-blue-500': tab }" @click="tab=1">
                <div class="m-auto">Comments</div>
            </div>
        </div>
        <div v-if="!tab" class="p-6 space-y-7 h-full flex flex-col">
            <div v-if="entity.owner === 'Me'">
                <div class="text-lg font-medium mb-4 ">Manage Access</div>
                <div class="flex flex-row">
                    <Button @click="showShareDialog=true">Share</Button>
                </div>
            </div>
            <div class="grow">
                <div class="text-lg font-medium mb-4">Properties</div>
                <div class="flex text-base">
                    <div class="w-1/2 text-gray-600 space-y-2">
                        <div>Type</div>
                        <div>Size</div>
                        <div>Modified</div>
                        <div>Created</div>
                        <div>Owner</div>
                    </div>
                    <div class="w-1/2 space-y-2">
                        <div>{{formattedMimeType}}</div>
                        <div>{{entity.file_size}}</div>
                        <div>{{entity.modified}}</div>
                        <div>{{entity.creation}}</div>
                        <div>{{entity.owner}}</div>
                    </div>
                </div>
            </div>
            <div class="text-gray-600 text-base">Viewers can download this file.</div>
        </div>
        <div v-else class="p-6 space-y-7 h-full flex flex-col">
        </div>
        <ShareDialog v-if="showShareDialog" v-model="showShareDialog" :entityName="entity.name"
            :isFolder="entity.is_group" />
    </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import ShareDialog from '@/components/ShareDialog.vue'
import { formatMimeType } from '@/utils/format'

export default {
    name: 'FileSidebar',
    components: {
        FeatherIcon,
        ShareDialog,
    },
    props: {
        entity: {
            type: Object,
            required: true,
        },
    },
    data() {
        return {
            tab: 0,
            showShareDialog: false,
        }
    },
    computed: {
        userId() {
            return this.$store.state.auth.user_id
        },
        formattedMimeType() {
            return this.entity.is_group ? "Folder" : formatMimeType(this.entity.mime_type)
        },
    }
} 
</script>