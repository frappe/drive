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
            required: false,
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
    resources: {
    },
}
</script>