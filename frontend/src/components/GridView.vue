<template>
    <div class="h-full flex flex-col" @click="deselectAll">
        <slot name="toolbar"></slot>
        <div v-if="isEmpty" class="flex-1">
            <slot name="placeholder"></slot>
        </div>
        <div v-else>
            <div class="mt-7" v-if="folders.length > 0">
                <div class="text-gray-600 font-medium">Folders</div>
                <div class="grid grid-cols-6 gap-6 my-3">
                    <div class="md:w-60 mt-1 rounded-lg border group select-none" v-for="folder in folders"
                        :key="folder.name" @click="selectEntity(folder, $event)"
                        :class="{ 'bg-blue-50': selectedEntities.includes(folder) }">
                        <div class="md:h-36 place-items-center grid">
                            <img src="/svgs/mime_types/folder.svg" />
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
                <div class="grid grid-cols-6 gap-6 my-3">
                    <div class="md:w-60 mt-1 rounded-lg border group select-none" v-for="file in files" :key="file.name"
                        @click="selectEntity(file, $event)" :class="{ 'bg-blue-50': selectedEntities.includes(file) }">
                        <div class="md:h-36 place-items-center grid">
                            <img :src="getMimeTypeIcon(file.mime_type)" />
                        </div>
                        <div class="px-3 pb-3">
                            <h3 class="truncate text-xl font-medium">{{ file.title }}</h3>
                            <div class="truncate text-base text-gray-600 flex mt-1">
                                <img :src="getMimeTypeIcon(file.mime_type)" class="h-5 mr-1" />
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

export default {
    name: 'GridView',
    components: {
        FeatherIcon,
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
            const mimeTypeArr = file.mime_type.split('/')
            const generics = ["image", "video", "audio"]
            const fileType = generics.includes(mimeTypeArr[0]) ? mimeTypeArr[0] : mimeTypeArr[1]
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
        getMimeTypeIcon(mimeType) {
            const image = new Image()
            const path = '/svgs/mime_types/';
            const mimeTypeArr = mimeType.split('/')
            let file = path + mimeTypeArr.join('-') + ".svg"
            image.src = file;
            if (image.width) return file;
            file = path + mimeTypeArr[0] + ".svg"
            image.src = file;
            if (image.width) return file;
            return path + "unknown.svg";
        }
    }
}
</script>