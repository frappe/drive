<template>
    <Dialog :options="{ title: 'Delete Forever?' }" v-model="open" >
        <template #body-content>
            <p class="text-gray-600">{{ entities.length === 1 ? `${entities.length} item` :
                    `${entities.length} items`
            }} will be deleted forever. This is an irreversible process.
            </p>
            <div class="flex mt-5">
                <Button @click="open = false" class="ml-auto"> Cancel </Button>
                <Button appearance="danger" iconLeft="trash-2" class="ml-4" @click="$resources.delete.submit()"
                    :loading="$resources.delete.loading">
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
        delete() {
            return {
                url: 'drive.api.files.delete_entities',
                params: {
                    entity_names: JSON.stringify(
                        this.entities?.map((entity) => entity.name)
                    ),
                },
                onSuccess(data) {
                    this.$emit('success', data)
                },
                onError(error) {
                    if (error.messages) {
                        console.log(error.messages);
                    }
                },
            }
        },
    },
}
</script>
