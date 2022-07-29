<template>
    <div class="h-full" @click="deselectAll">
        <slot name="toolbar"></slot>
        <div v-if="isEmpty" class="flex-1">
            <slot name="placeholder"></slot>
        </div>
        <div v-else>
            <div class="mt-7" v-if="folders.length > 0">
                <div class="text-gray-600 font-medium">Folders</div>
                <div class="grid grid-cols-7 gap-4 my-2">
                    <div class="md:w-52 mt-1 rounded-lg border group" v-for="folder in folders" :key="folder.name"
                        @click="selectEntity(folder, $event)"
                        :class="{ 'bg-blue-50': selectedEntities.includes(folder) }">
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
                    <div class="md:w-52 mt-1 rounded-lg border group" v-for="file in files" :key="file.name"
                        @click="selectEntity(file, $event)" :class="{ 'bg-blue-50': selectedEntities.includes(file) }">
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
    data() {
        return {
            selectedEntities: []
        }
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
            let folders = []
            if (this.folderContents)
                folders = this.folderContents.filter(x => x.is_group === 1)
            return folders
        },
        files() {
            let files = []
            if (this.folderContents)
                files = this.folderContents.filter(x => x.is_group === 0)
            return files
        }
    },
    methods: {
        getFileSubtitle(file) {
            const fileType = file.mime_type.split('/')[1]
            return `${fileType.charAt(0).toUpperCase() + fileType.slice(1)} ∙ ${file.modified}`
        },
        selectEntity(entity, event) {
            event.stopPropagation()
            if (event.ctrlKey) {
                const index = this.selectedEntities.indexOf(entity)
                if (index > -1) this.selectedEntities.splice(index, 1)
                else this.selectedEntities.push(entity)
            }
            else {
                if (this.selectedEntities.length === 1 && this.selectedEntities[0] === entity)
                    this.$emit('openEntity', entity)
                else this.selectedEntities = [entity]
            }
            this.$emit('entitySelected', this.selectedEntities)
        },
        deselectAll() {
            this.selectedEntities = []
            this.$emit('entitySelected', this.selectedEntities)
        },
    }
}
</script>