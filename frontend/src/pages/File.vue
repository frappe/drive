<template>
    <div class="h-full">
        <div class="py-3 px-5 h-16 md:h-12 z-10 flex items-center justify-between border-b">
            <h3 class="truncate font-medium">{{ $resources.file.data?.title }}</h3>
            <div class="flex items-center">
                <div class="relative ml-3">
                    <Dropdown :options="actionItems" placement="right">
                        <button
                            class="flex items-center max-w-xs text-sm text-white rounded-full focus:outline-none focus:shadow-solid"
                            id="actions-menu" aria-label="Actions menu" aria-haspopup="true">
                            <div class="flex items-center gap-4">
                                <Button appearance="minimal" icon="more-vertical"></Button>
                            </div>
                        </button>
                    </Dropdown>
                </div>
                <div class="relative ml-3">
                    <Dropdown :options="dropdownItems" placement="right">
                        <button
                            class="flex items-center max-w-xs text-sm text-white rounded-full focus:outline-none focus:shadow-solid"
                            id="user-menu" aria-label="User menu" aria-haspopup="true">
                            <div class="flex items-center gap-4">
                                <Avatar :label="fullName" :imageURL="imageURL" />
                            </div>
                        </button>
                    </Dropdown>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

import { Avatar, Dropdown } from 'frappe-ui'

export default {
    name: 'File',
    components: {
        Avatar,
        Dropdown,
    },
    data() {
        return {
            dropdownItems: [
                {
                    label: 'Log out',
                    handler: () => this.$store.dispatch('logout'),
                },
            ],
            actionItems: [
                {
                    label: 'Download',
                    handler: () => {
                        window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.entityName}&trigger_download=1`
                    },
                },
            ]
        }
    },
    props: {
        entityName: {
            type: String,
            required: true,
            default: '',
        },
    },
    computed: {
        userId() {
            return this.$store.state.auth.user_id
        },
        fullName() {
            return this.$store.state.user.fullName
        },
        imageURL() {
            return this.$store.state.user.imageURL
        },
    },
    methods: {
    },
    created() {
        this.$resources.file.fetch()
    },
    resources: {
        file() {
            return {
                method: 'drive.api.permissions.get_file_with_permissions',
                params: { entity_name: this.entityName, },
                onSuccess(data) {
                    this.$resources.file.data = data
                },
            }
        },
    },
}
</script>