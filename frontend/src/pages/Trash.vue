<template>
    <div class="h-full">
        <FolderContentsError v-if="$resources.folderContents.error" :error="$resources.folderContents.error" />

        <GridView v-else-if="$store.state.view === 'grid'" :folderContents="$resources.folderContents.data"
            :selectedEntities="selectedEntities" @entitySelected="(selected) => (selectedEntities = selected)">
            <template #toolbar>
                <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :columnHeaders="columnHeaders"
                    :actionLoading="actionLoading" :showUploadButton="false" :showViewButton="false" />
            </template>
            <template #placeholder>
                <NoFilesSection />
            </template>
        </GridView>

        <ListView v-else :folderContents="$resources.folderContents.data" :selectedEntities="selectedEntities"
            @entitySelected="(selected) => (selectedEntities = selected)">
            <template #toolbar>
                <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :columnHeaders="columnHeaders"
                    :actionLoading="actionLoading" :showUploadButton="false" :showViewButton="false" />
            </template>
            <template #placeholder>
                <NoFilesSection />
            </template>
        </ListView>
        <div />
    </div>
</template>

<script>
import DriveToolBar from '@/components/DriveToolBar.vue'
import FolderContentsError from '@/components/FolderContentsError.vue'
import GridView from '@/components/GridView.vue'
import ListView from '@/components/ListView.vue'
import NoFilesSection from '@/components/NoFilesSection.vue'
import { formatDate, formatSize } from '@/utils/format'
import { FeatherIcon } from 'frappe-ui'

export default {
    name: 'Trash',
    components: {
        FeatherIcon,
        ListView,
        GridView,
        DriveToolBar,
        NoFilesSection,
        FolderContentsError,
    },
    data: () => ({
        selectedEntities: [],
        breadcrumbs: [{ label: 'Trash', route: '/trash' }],
        actionLoading: false,
    }),
    computed: {
        userId() {
            return this.$store.state.auth.user_id
        },
        orderBy() {
            return this.$store.state.sortOrder.ascending
                ? this.$store.state.sortOrder.field
                : `${this.$store.state.sortOrder.field} desc`
        },
        actionItems() {
            return [
                {
                    label: 'Empty Trash',
                    handler: () => {
                        console.log("Hello");
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length === 0
                    },
                },
                {
                    label: 'Delete Forever',
                    handler: () => {
                        this.actionLoading = true
                        this.$resources.deleteEntities.submit()
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length > 0
                    },
                },
                {
                    label: 'Restore',
                    handler: () => {
                        console.log("hello");
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length > 0
                    },
                },
            ].filter((item) => item.isEnabled())
        },
        columnHeaders() {
            return [
                {
                    label: 'Name',
                    field: 'title',
                    sortable: true,
                },
                {
                    label: 'Owner',
                    field: 'owner',
                    sortable: true,
                },
                {
                    label: 'Modified',
                    field: 'modified',
                    sortable: true,
                },
                {
                    label: 'Size',
                    field: 'file_size',
                    sortable: true,
                },
            ].filter((item) => item.sortable)
        },
    },
    resources: {
        folderContents() {
            return {
                method: 'drive.api.files.list_folder_contents',
                cache: ['folderContents', this.entityName],
                params: {
                    entity_name: this.entityName,
                    order_by: this.orderBy,
                    fields: [
                        'name',
                        'title',
                        'is_group',
                        'owner',
                        'modified',
                        'file_size',
                        'mime_type',
                        'creation',
                    ],
                },
                onSuccess(data) {
                    this.$resources.folderContents.error = null
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
                auto: true,
            }
        },
        deleteEntities() {
            return {
                method: 'drive.api.files.delete_entities',
                params: {
                    entity_names: JSON.stringify(
                        this.selectedEntities.map((entity) => entity.name)
                    ),
                },
                onSuccess() {
                    this.actionLoading = false
                    this.$resources.folderContents.fetch()
                    this.selectedEntities = []
                },
            }
        },
    },
}
</script>