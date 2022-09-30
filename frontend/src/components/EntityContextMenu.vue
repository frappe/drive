<template>
	<div
		class="bg-gray-100"
		:style="{ left: `${entityContext.x}px`, top: `${entityContext.y}px` }"
		v-if="contextActionItems.length > 0"
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
		}
	}
}
</script>
<style scoped>
div {
	position: absolute;
	width: auto;
	z-index: 250;
	padding: 0.5rem 1rem 0.5em 1rem;
	cursor: pointer;
}
li {
	height: 1.5rem;
	width: auto;
}
li:hover {
	text-decoration: underline;
}
</style>