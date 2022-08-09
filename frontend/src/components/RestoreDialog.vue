<template>
    <Dialog :options="{ title: 'Restore Items?' }" v-model="open">
        <template #body-content>
            <p class="text-gray-600">Selected items will be restored to their original locations.</p>
            <div class="flex mt-5">
                <Button @click="open = false" class="ml-auto"> Cancel </Button>
                <Button appearance="primary" iconLeft="refresh-ccw" class="ml-4" @click="$resources.restore.submit()"
                    :loading="$resources.restore.loading">
                    Restore
                </Button>
            </div>
        </template>
    </Dialog>
</template>
<script>
import { Dialog, Input } from 'frappe-ui'

export default {
    name: 'RestoreDialog',
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
        restore() {
            return {
                method: 'drive.api.files.toggle_is_active',
                params: {
                    entity_names: JSON.stringify(
                        this.entities.map((entity) => entity.name)
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

