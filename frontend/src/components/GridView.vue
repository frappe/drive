<template>
    <div class="h-full flex flex-col">
        <slot name="toolbar"></slot>
        <div v-if="isEmpty" class="flex-1">
            <slot name="placeholder"></slot>
        </div>
        <div v-else class="h-full px-5 md:px-0" @click="deselectAll">
            <div class="mt-7" v-if="folders.length > 0">
                <div class="text-gray-600 font-medium">Folders</div>
                <div class="flex flex-row flex-wrap gap-5 my-4">
                    <div class="md:w-60 rounded-lg border group select-none" v-for="folder in folders"
                        :key="folder.name" @click="selectEntity(folder, $event)"
                        @contextmenu="handleEntityContext(folder, $event)"
                        :class="{ 'bg-blue-50': selectedEntities.includes(folder) }">
                        <div class="h-28 md:h-36 place-items-center grid">
                            <Folder />
                        </div>
                        <div class="px-3 pb-3">
                            <h3 class="truncate text-xl font-medium">{{ folder.title }}</h3>
                            <p class="truncate text-base text-gray-600 mt-1">{{ folder.modified }}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-7" v-if="files.length > 0">
                <div class="text-gray-600 font-medium">Files</div>
                <div class="flex flex-row flex-wrap gap-5 my-4">
                    <div class="md:w-60 rounded-lg border group select-none" v-for="file in files" :key="file.name"
                        @click="selectEntity(file, $event)" :class="{ 'bg-blue-50': selectedEntities.includes(file) }"
                        @contextmenu="handleEntityContext(file, $event)">
                        <div class="h-28 md:h-36 place-items-center grid">
                            <component :is="getMimeTypeComp(file.mime_type)" />
                        </div>
                        <div class="px-3 pb-3">
                            <h3 class="truncate text-xl font-medium">{{ file.title }}</h3>
                            <div class="truncate text-base text-gray-600 flex mt-1">
                                <!-- <img :src="getMimeTypeIcon(file.mime_type)" class="h-5 mr-1" /> -->
                                <p>{{ getFileSubtitle(file) }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import Folder from './mime-types/Folder.vue'
import * as mimeTypes from './mime-types/index.vue'
import { formatMimeType } from '@/utils/format'

export default {
    name: 'GridView',
    components: {
        FeatherIcon,
        Folder,
    },
    props: {
        folderContents: {
            type: Array,
        },
        selectedEntities: {
            type: Array,
        },
    },
    computed: {
        isEmpty() {
            return this.folderContents && this.folderContents.length === 0
        },
        folders() {
            return this.folderContents ? this.folderContents.filter(x => x.is_group === 1) : []
        },
        files() {
            return this.folderContents ? this.folderContents.filter(x => x.is_group === 0) : []
        }
    },
    emits: ['entitySelected', 'openEntity', 'showEntityContext'],
    methods: {
        getFileSubtitle(file) {
            const fileSubtitle = formatMimeType(file.mime_type)
            return `${fileSubtitle} ∙ ${file.modified}`
        },
        selectEntity(entity, event) {
            event.stopPropagation()
            let selectedEntities = this.selectedEntities
            if (event.ctrlKey) {
                const index = selectedEntities.indexOf(entity)
                index > -1 ? selectedEntities.splice(index, 1) : selectedEntities.push(entity)
                this.$emit('entitySelected', selectedEntities)
            }
            else {
                if (selectedEntities.length === 1 && selectedEntities[0] === entity) {
                    this.$emit('openEntity', entity)
                    if (entity.is_group === 1) this.deselectAll()
                }
                else {
                    selectedEntities = [entity]
                    this.$emit('entitySelected', selectedEntities)
                }
            }
            this.$store.commit('setEntityInfo', selectedEntities[selectedEntities.length - 1])
        },
        deselectAll() {
            this.$emit('entitySelected', [])
            this.$store.commit('setEntityInfo', null)
        },
        getMimeTypeComp(mimeType) {
            let componentName = "Unknown"
            if (mimeType) {
                const mimeTypeArr = mimeType.split('/').map(x => x.charAt(0).toUpperCase() + x.slice(1))
                if (mimeTypeArr.join('') in mimeTypes)
                    componentName = mimeTypeArr.join('')
                else if (mimeTypeArr[0] in mimeTypes)
                    componentName = mimeTypeArr[0]
            }
            return mimeTypes[componentName]
        },
        handleEntityContext(entity, event) {
            this.$emit('entitySelected', [entity])
            this.$store.commit('setEntityInfo', entity)
            this.$emit('showEntityContext', { x: event.clientX, y: event.clientY })
            event.preventDefault()
        },
    }
}
</script>