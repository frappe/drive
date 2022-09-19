<template>
    <div class="w-96 border-l">
        <div class="h-11 flex cursor-pointer text-base">
            <div class="w-1/2 flex border-b" :class="{ 'text-gray-500': tab, 'border-blue-500': !tab }" @click="tab=0">
                <div class="m-auto">Detail</div>
            </div>
            <div class="w-1/2 flex border-b" :class="{ 'text-gray-500': !tab, 'border-blue-500': tab }" @click="tab=1">
                <div class="m-auto">Comments</div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'FileSideBar',
    data() {
        return {
            tab: 0
        }
    }
} 
</script>