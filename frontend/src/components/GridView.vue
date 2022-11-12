<template>
    <div class="h-full flex flex-col">
        <slot name="toolbar"></slot>
        <div v-if="isEmpty" class="flex-1">
            <slot name="placeholder"></slot>
        </div>
        <div v-else class="h-full px-5 md:px-0" @click="deselectAll" v-on-outside-click="deselectAll">
            <div class="mt-3" v-if="folders.length > 0">
                <div class="text-gray-600 font-medium">Folders</div>
                <div class="flex flex-row flex-wrap gap-5 mt-4">
                    <div class="md:w-[212px] rounded-lg border group select-none" v-for="folder in folders"
                        :key="folder.name" @click="selectEntity(folder, $event)"
                        @contextmenu="handleEntityContext(folder, $event)"
                        :class="{ 'bg-blue-50': selectedEntities.includes(folder) }">
                        <div class="h-28 md:h-32 place-items-center grid">
                            <img src="/src/assets/images/icons/folder.svg" />
                        </div>
                        <div class="px-3.5 pb-2.5">
                            <h3 class="truncate text-[14px] font-medium">{{ folder.title }}</h3>
                            <p class="truncate text-sm text-gray-600 mt-1">{{ folder.modified }}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div :class="folders.length > 0 ? 'mt-8' : 'mt-3'" v-if="files.length > 0">
                <div class="text-gray-600 font-medium">Files</div>
                <div class="flex flex-row flex-wrap gap-5 mt-4">
                    <div class="md:w-[212px] rounded-lg border group select-none" v-for="file in files" :key="file.name"
                        @click="selectEntity(file, $event)" :class="{ 'bg-blue-50': selectedEntities.includes(file) }"
                        @contextmenu="handleEntityContext(file, $event)">
                        <div class="h-28 md:h-32 place-items-center grid">
                            <img :src="getIconUrl(formatMimeType(file.mime_type))" class="h-14" />
                        </div>
                        <div class="px-3.5 md:h-16 content-center grid">
                            <h3 class="truncate text-[14px] font-medium">{{ file.title }}</h3>
                            <div class="truncate text-sm text-gray-600 flex mt-1 place-items-center">
                                <img :src="getIconUrl(formatMimeType(file.mime_type))" class="h-3.5 mr-1.5" />
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
import { formatMimeType } from '@/utils/format'
import getIconUrl from '@/utils/getIconUrl'

export default {
    name: 'GridView',
    components: {
        FeatherIcon,
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
            let fileSubtitle = formatMimeType(file.mime_type)
            fileSubtitle = fileSubtitle.charAt(0).toUpperCase() + fileSubtitle.slice(1)
            return `${fileSubtitle} ∙ ${file.modified}`
        },
        selectEntity(entity, event) {
            event.stopPropagation()
            this.$emit('showEntityContext', null)
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
            this.$emit('showEntityContext', null)
        },
        handleEntityContext(entity, event) {
            this.$emit('entitySelected', [entity])
            this.$store.commit('setEntityInfo', entity)
            this.$emit('showEntityContext', { x: event.clientX, y: event.clientY })
            event.preventDefault()
        },
    },
    setup() {
        return { formatMimeType, getIconUrl }
    }
}
</script>