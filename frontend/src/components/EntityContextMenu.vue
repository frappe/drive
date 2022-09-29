<template>
	<div
		class="bg-gray-100"
		:style="{ left: `${entityContext.x}px`, top: `${entityContext.y}px` }"
	>
		<ul>
		<li
			v-for="(item, index) in contextActionItems"
			:key="index"
			class="text-sm h-8"
			@click="closeAndApply(item.handler)"
			>
			{{ item.label }}
		</li>
	</ul>
	</div>
</template>
<script>
	// <Dialog>
	// </Dialog>
import { Dialog, Button, ListItem } from 'frappe-ui'
export default {
	name: 'EntityContextMenu',
  components: { Dialog, Button, ListItem },
  props: {
		actionItems: {
			type: Array,
		},
		entityContext: {
			type: Object,
		},
	},
	computed: {
		contextActionItems(){
			console.log(JSON.stringify(this.$props))
			if (this.actionItems.length <= 2){
				return []
			} else {
				return this.actionItems
			}
		}
	},
	methods: {
		closeAndApply(handler){
			handler()
			this.$emit('showEntityContext')
		}
	}
}
</script>
<style scoped>
div {
	position: absolute;
	width: auto;
	z-index: 250;
	padding: 1rem;
}
li {
	height: 1.5rem;
	width: auto;
}
li:hover {
	text-decoration: underline;
}
</style>