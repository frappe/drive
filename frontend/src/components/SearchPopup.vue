<template>
    <div :class="divClass">
        <Input iconLeft="search" type="text" v-model="search" placeholder="Search" @focus="openPopup = true" />
        <div v-if="showEntities" v-for="entity in filteredEntities" @click="openEntity(entity)"
            class="flex flex-row cursor-pointer hover:bg-gray-100 rounded-md py-2 px-3">
            <div class="flex grow items-center">
                <img :src="`/src/assets/images/icons/${entity.is_group ? 'folder'
                : formatMimeType(entity.mime_type)}.svg`" class="w-6 mr-4" />
                <div class="w-72">
                    <div class="text-lg text-gray-900 font-medium truncate">{{ entity.title }}</div>
                    <div class="text-[13px] text-gray-600">{{ entity.owner }}</div>
                </div>
            </div>
            <div class="text-[13px] text-gray-600 whitespace-nowrap my-auto">{{ entity.modified }}</div>
        </div>
    </div>
</template>
<script>
import { Input } from 'frappe-ui'
import { formatSize, formatDate } from '@/utils/format'
import getFilteredEntities from '../utils/fuzzySearcher'
import { formatMimeType } from '@/utils/format'

export default {
    name: 'SearchPopup',
    components: {
        Input,
    },
    props: {
        modelValue: {
            type: Boolean,
            required: true,
        },
    },
    emits: ['update:modelValue', 'openEntity'],
    data() {
        return {
            search: '',
            openPopup: false,
        }
    },
    computed: {
        divClass() {
            if (!this.openPopup) return "w-[200px]"
            return "w-[620px] border rounded-xl shadow-md p-2"
        },
        userId() {
            return this.$store.state.auth.user_id
        },
        filteredEntities() {
            return getFilteredEntities(this.search, this.$resources.entities.data)
        },
        showEntities() {
            return this.search.length > 0
        },
        open: {
            get() {
                return this.modelValue
            },
            set(value) {
                this.$emit('update:modelValue', value)
            },
        },
    },
    methods: {
        openEntity(entity) {
            this.$emit('openEntity', entity)
            this.open = false
        },
    },
    setup() {
        return { formatMimeType }
    },
    resources: {
        entities() {
            return {
                method: 'drive.api.permissions.get_all_my_entities',
                onSuccess(data) {
                    this.$resources.entities.error = null
                    data.forEach((entity) => {
                        entity.size_in_bytes = entity.file_size
                        entity.file_size = entity.is_group
                            ? '-'
                            : formatSize(entity.file_size)
                        entity.modified = formatDate(entity.modified)
                        entity.creation = formatDate(entity.creation)
                        entity.owner = entity.owner === this.userId ? 'me' : entity.owner
                    })
                },
            }
        },
    },
}
</script>


