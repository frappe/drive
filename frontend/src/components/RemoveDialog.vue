<template>
    <Dialog :options="{ title: 'Move to Trash?' }" v-model="open">
        <template #body-content>
            <p class="text-gray-600">{{ entities.length === 1 ? `${entities.length} item` : `${entities.length} items`
            }}
                will be moved to Trash. Items in Trash are deleted forever after 30 days.
            </p>
            <div class="flex mt-5">
                <Button @click="open = false" class="ml-auto"> Cancel </Button>
                <Button appearance="primary" iconLeft="trash-2" class="ml-4" @click="$resources.remove.submit()"
                    :loading="$resources.remove.loading">
                    Move to Trash
                </Button>
            </div>
        </template>
    </Dialog>
</template>
<script>
import { Dialog, Input } from 'frappe-ui'

export default {
    name: 'RemoveDialog',
    components: {
        Dialog,
        Input,
    },
    props: {
        modelValue: {
            type: Boolean,
            required: true,
        },
        entities: {
            type: Array,
            required: true,
        },
    },
    emits: ['update:modelValue', 'success'],
    computed: {
        open: {
            get() {
                return this.modelValue
            },
            set(value) {
                this.$emit('update:modelValue', value)
            },
        },
    },
    resources: {
        remove() {
            return {
                // method: 'drive.api.files.call_controller_method',
                // params: {
                //     method: 'rename',
                //     entity_name: this.entityName,
                //     new_title: this.newName,
                // },
                // validate(params) {
                //     if (!params?.new_title) {
                //         return 'New name is required'
                //     }
                // },
                // onSuccess(data) {
                //     this.newName = ''
                //     this.$emit('success', data)
                // },
                // onError(error) {
                //     if (error.messages) {
                //         this.errorMessage = error.messages.join('\n')
                //     } else {
                //         this.errorMessage = error.message
                //     }
                // },
            }
        },
    },
}
</script>
