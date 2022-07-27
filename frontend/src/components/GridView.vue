<template>
    <div class="h-full">
        <slot name="toolbar"></slot>
        <div v-if="isEmpty" class="flex-1">
            <slot name="placeholder"></slot>
        </div>
        <div v-else>
            <div class="mt-7">
                <div class="text-gray-600 font-medium">Folders</div>
                <div class="grid grid-cols-6 gap-5 my-2">
                    <div class="md:h-44 md:w-60 mt-1 rounded-lg border-2"></div>
                </div>
            </div>
            <div class="mt-7">
                <div class="text-gray-600 font-medium">Files</div>
                <div class="grid grid-cols-6 gap-5 my-2">
                    <div class="md:h-52 md:w-60 mt-1 rounded-lg border-2"></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'GridView',
    props: {
        folderContents: {
            type: Array,
        },
    },
    computed: {
        isEmpty() {
            return this.folderContents && this.folderContents.length === 0
        },
    },
}
</script>