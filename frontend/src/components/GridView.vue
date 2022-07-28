<template>
    <div class="h-full">
        <slot name="toolbar"></slot>
        <div v-if="isEmpty" class="flex-1">
            <slot name="placeholder"></slot>
        </div>
        <div v-else>
            <div class="mt-7" v-if="folders.length > 0">
                <div class="text-gray-600 font-medium">Folders</div>
                <div class="grid grid-cols-7 gap-4 my-2">
                    <div class="md:w-52 mt-1 rounded-lg border-2 group" v-for="folder in folders">
                        <div class="h-7 pt-3">
                            <FeatherIcon name="more-horizontal" :strokeWidth="2"
                                class="w-4 h-4 row-span-1 text-gray-700 mr-4 ml-auto hidden group-hover:block" />
                        </div>
                        <div class="md:h-28 place-items-center grid">
                            <Folder />
                        </div>
                        <div class="p-3">
                            <h3 class="truncate text-lg font-medium">{{ folder.title }}</h3>
                            <p class="truncate text-sm text-gray-600">{{ folder.modified }}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-7" v-if="files.length > 0">
                <div class="text-gray-600 font-medium">Files</div>
                <div class="grid grid-cols-7 gap-4 my-2">
                    <div class="md:w-52 mt-1 rounded-lg border-2 group" v-for="file in files">
                        <div class="h-7 pt-3">
                            <FeatherIcon name="more-horizontal" :strokeWidth="2"
                                class="w-4 h-4 row-span-1 text-gray-700 mr-4 ml-auto hidden group-hover:block" />
                        </div>
                        <div class="md:h-32">
                        </div>
                        <div class="p-3">
                            <h3 class="truncate text-lg font-medium">{{ file.title }}</h3>
                            <p class="truncate text-sm text-gray-600">{{ getFileSubtitle(file) }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import Folder from '../assets/svgs/folder.vue';

export default {
    name: 'GridView',
    components: {
        FeatherIcon,
        Folder
    },
    props: {
        folderContents: {
            type: Array,
        },
    },
    computed: {
        isEmpty() {
            return this.folderContents && this.folderContents.length === 0
        },
        folders() {
            return this.folderContents.filter(x => x.is_group === 1)
        },
        files() {
            return this.folderContents.filter(x => x.is_group === 0)
        }
    },
    methods: {
        getFileSubtitle(file) {
            const fileType = file.mime_type.split('/')[1]
            return `${fileType.charAt(0).toUpperCase() + fileType.slice(1)} ∙ ${file.modified}`
        }
    }
}
</script>