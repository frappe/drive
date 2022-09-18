<template>
    <div class="h-full">Hello</div>
</template>

<script>

export default {
    name: 'File',
    components: {
    },
    props: {
        entityName: {
            type: String,
            required: true,
            default: '',
        },
    },
    data: () => ({
    }),
    computed: {
        userId() {
            return this.$store.state.auth.user_id
        },
    },
    methods: {
    },
    mounted() {
        this.$resources.entity.fetch()
    },
    resources: {
        file() {
            return {
                method: 'drive.api.permissions.get_file_with_permissions',
                params: { entity_name: this.entityName, },
                onSuccess(data) {
                    console.log(data)
                    this.generalAccess = data
                },
            }
        },
    },
}
</script>