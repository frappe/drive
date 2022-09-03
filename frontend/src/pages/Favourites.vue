<template>
    <div class="h-full">
        <FolderContentsError v-if="$resources.folderContents.error" :error="$resources.folderContents.error" />

        <GridView v-else-if="$store.state.view === 'grid'" :folderContents="$resources.folderContents.data"
            :selectedEntities="selectedEntities" @entitySelected="(selected) => (selectedEntities = selected)"
            @openEntity="(entity) => openEntity(entity)">
            <template #toolbar>
                <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :columnHeaders="columnHeaders"
                    :actionLoading="actionLoading" :showUploadButton="false" :showViewButton="false" />
            </template>
            <template #placeholder>
                <NoFilesSection :primaryMessage="`You haven't favourited any items`"
                    :secondaryMessage="'Items will appear here for easy access when you add them to favourites'" />
            </template>
        </GridView>

        <ListView v-else :folderContents="$resources.folderContents.data" :selectedEntities="selectedEntities"
            @entitySelected="(selected) => (selectedEntities = selected)" @openEntity="(entity) => openEntity(entity)">
            <template #toolbar>
                <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :columnHeaders="columnHeaders"
                    :actionLoading="actionLoading" :showUploadButton="false" :showViewButton="false" />
            </template>
            <template #placeholder>
                <NoFilesSection :primaryMessage="`You haven't favourited any items`"
                    :secondaryMessage="'Items will appear here for easy access when you add them to favourites'" />
            </template>
        </ListView>

        <FilePreview v-if="showPreview" @hide="hidePreview" :previewEntity="previewEntity" />

        <RenameDialog v-model="showRenameDialog" :entity="selectedEntities[0]" @success="
            () => {
                $resources.folderContents.fetch()
                showRenameDialog = false
                selectedEntities = []
            }
        " />
        <GeneralDialog v-model="showRemoveDialog" :entities="selectedEntities" :for="'remove'" @success="
            () => {
                $resources.folderContents.fetch()
                showRemoveDialog = false
                selectedEntities = []
            }
        " />
        <ShareDialog v-if="showShareDialog" v-model="showShareDialog" :entityName="selectedEntities[0].name" />
        <DetailsDialog v-model="showDetailsDialog" :entity="selectedEntities[0]" />
        <div />

    </div>
</template>

<script>
import DriveToolBar from '@/components/DriveToolBar.vue'
import FolderContentsError from '@/components/FolderContentsError.vue'
import GridView from '@/components/GridView.vue'
import ListView from '@/components/ListView.vue'
import FilePreview from '@/components/FilePreview.vue'
import GeneralDialog from '@/components/GeneralDialog.vue'
import RenameDialog from '@/components/RenameDialog.vue'
import ShareDialog from '@/components/ShareDialog.vue'
import DetailsDialog from '@/components/DetailsDialog.vue'
import NoFilesSection from '@/components/NoFilesSection.vue'
import { formatDate, formatSize } from '@/utils/format'
import { FeatherIcon } from 'frappe-ui'

export default {
    name: 'Favourites',
    components: {
        FeatherIcon,
        ListView,
        GridView,
        FilePreview,
        DriveToolBar,
        GeneralDialog,
        RenameDialog,
        ShareDialog,
        DetailsDialog,
        NoFilesSection,
        FolderContentsError,
    },
    data: () => ({
        selectedEntities: [],
        previewEntity: null,
        showPreview: false,
        breadcrumbs: [{ label: 'Favourites', route: '/favourites' }],
        actionLoading: false,
        showRenameDialog: false,
        showShareDialog: false,
        showDetailsDialog: false,
        showRemoveDialog: false,
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
                    label: 'Download',
                    handler: () => {
                        window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`
                    },
                    isEnabled: () => {
                        return (
                            this.selectedEntities.length === 1 &&
                            !this.selectedEntities[0].is_group
                        )
                    },
                },
                {
                    label: 'Share',
                    handler: () => {
                        this.showShareDialog = true
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length === 1
                    },
                },
                {
                    label: 'Details',
                    handler: () => {
                        this.showDetailsDialog = true
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length === 1
                    },
                },
                {
                    label: 'Rename',
                    handler: () => {
                        this.showRenameDialog = true
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length === 1
                    },
                },
                {
                    label: 'Remove from Favourites',
                    handler: () => {
                        this.$resources.toggleFavourite.submit()
                    },
                    isEnabled: () => {
                        return this.selectedEntities.length > 0
                    },
                },
                {
                    label: 'Move to Trash',
                    handler: () => {
                        this.showRemoveDialog = true
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

    methods: {
        openEntity(entity) {
            if (entity.is_group) {
                this.selectedEntities = []
                this.$router.push({
                    name: 'Folder',
                    params: { entityName: entity.name },
                })
            } else {
                this.previewEntity = entity
                this.showPreview = true
            }
        },
        hidePreview() {
            this.showPreview = false
            this.previewEntity = null
        },
    },

    resources: {
        folderContents() {
            return {
                method: 'drive.api.files.list_folder_contents',
                params: {
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
                    is_favourite: 1,
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
        toggleFavourite() {
            return {
                method: 'drive.api.files.favourite_entities',
                params: {
                    entity_names: JSON.stringify(
                        this.selectedEntities?.map((entity) => entity.name)
                    ),
                },
                onSuccess() {
                    this.$resources.folderContents.fetch()
                    this.selectedEntities = []
                },
                onError(error) {
                    if (error.messages) {
                        console.log(error.messages);
                    }
                },
            }
        },
    },
}
</script>
