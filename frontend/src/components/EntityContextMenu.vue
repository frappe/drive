<template>
	<div class="bg-white rounded-xl absolute shadow-md p-2 w-56 z-50 space-y-0.5"
		:style="{ left: `${entityContext.x}px`, top: `${entityContext.y}px` }" v-if="contextActionItems.length > 0">
		<div v-for="(item, index) in contextActionItems" :key="index"
			class="text-sm h-7 hover:bg-gray-100 cursor-pointer rounded-lg flex px-3 items-center" @click="closeAndApply(item.handler)">
			<FeatherIcon :name="item.icon" :strokeWidth="1" class="w-4 h-4 text-gray-700 mr-3" />
			<div class="text-gray-800 text-base">{{ item.label }}</div>
		</div>
	</div>
</template>
<script>
import { FeatherIcon } from 'frappe-ui'

export default {
	name: 'EntityContextMenu',
	components: { FeatherIcon },
	props: {
		actionItems: {
			type: Array,
		},
		entityContext: {
			type: Object,
		},
	},
	computed: {
		contextActionItems() {
			console.log(this.actionItems)
			if (this.actionItems[0].label === 'New Folder') {
				return []
			} else {
				return this.actionItems
			}
		}
	},
	methods: {
		closeAndApply(handler) {
			handler()
		}
	}
}
</script>