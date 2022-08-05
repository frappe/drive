<template>
    <Dialog :options="{ title: 'Delete Forever?' }" v-model="open">
        <template #body-content>
            <p class="text-gray-600">{{ entities.length === 1 ? `${entities.length} item` : `${entities.length} items`
            }}
                will be deleted forever. This is an irreversible process.
            </p>
            <div class="flex mt-5">
                <Button @click="open = false" class="ml-auto"> Cancel </Button>
                <Button appearance="primary" class="ml-4" @click="$resources.remove.submit()"
                    :loading="$resources.remove.loading">
                    Delete Forever
                </Button>
            </div>
        </template>
    </Dialog>
</template>
<script>
import { Dialog, Input } from 'frappe-ui'

export default {
    name: 'DeleteDialog',
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
