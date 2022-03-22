<template>
  <Dialog :options="{ title: 'Sharing options' }" v-model="open">
    <template #dialog-content>
      <div class="text-left min-w-[16rem]" ref="dialogContent">
        <div class="flex mt-5 text-xs text-gray-500">
          <FeatherIcon
            name="user-plus"
            :strokeWidth="2"
            class="h-4 pr-1"
          />Shared with
        </div>
        <div
          v-for="user in $resources.sharedWith.data"
          :key="user.user"
          class="mt-3 flex justify-between items-center text-base text-gray-600 font-medium antialiased"
        >
          <div class="flex w-full gap-2 items-center">
            <div class="overflow-hidden rounded-full h-7 w-7">
              <img
                v-if="user.user_image"
                :src="user.user_image"
                class="object-cover rounded-full h-7 w-7"
              />
              <div
                v-else
                class="flex items-center justify-center w-full h-full text-base text-gray-600 uppercase bg-gray-200"
              >
                {{ user.full_name[0] }}
              </div>
            </div>
            <div class="max-w-[70%] truncate">{{ user.user }}</div>
          </div>
          <Dropdown
            placement="right"
            :options="
              [
                { label: 'Editor' },
                { label: 'Viewer' },
                { label: 'Delete' },
              ].map((option) => ({
                ...option,
                handler: () => {
                  user.loading = true
                  $resources.share
                    .submit(
                      Object.assign(
                        {
                          method:
                            option.label === 'Delete' ? 'unshare' : 'share',
                          entity_name: entityName,
                          user: user.user,
                        },
                        option.label != 'Delete' && {
                          write: option.label === 'Editor' ? 1 : 0,
                        }
                      )
                    )
                    .then(() => {
                      user.loading = false
                    })
                },
              }))
            "
          >
            <Button
              iconRight="chevron-down"
              :loading="user.loading"
              class="text-sm w-24 focus:ring-0 focus:ring-offset-0"
              >{{ user.write ? 'Editor' : 'Viewer' }}</Button
            >
          </Dropdown>
        </div>
        <Button
          v-if="!showUserSearch"
          class="mt-5 focus:ring-0 focus:ring-offset-0"
          icon="plus"
          @click="showUserSearch = true"
        />
        <div
          v-if="showUserSearch"
          class="flex items-start mt-5 gap-2 w-full relative"
        >
          <UserSearch class="flex-1 invisible" />
          <UserSearch
            v-model="searchQuery"
            @submit="
              (user) =>
                $resources.share.submit({
                  method: 'share',
                  entity_name: entityName,
                  user: user,
                  write: 1,
                })
            "
            class="flex-1 absolute w-[calc(100%_-_2.25rem)]"
          />
          <Button
            class="focus:ring-0 focus:ring-offset-0 absolute left-[calc(100%_-_1.75rem)]"
            icon="plus"
            type="primary"
            @click="$resources.share.fetch()"
          />
        </div>
        <ErrorMessage
          v-if="$resources.share.error"
          class="mt-2"
          :message="errorMessage"
        />
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, ErrorMessage, FeatherIcon, Button } from 'frappe-ui'
import UserSearch from '@/components/UserSearch.vue'
import Dropdown from '@/components/Dropdown.vue'

export default {
  name: 'ShareDialog',
  components: {
    Dialog,
    ErrorMessage,
    FeatherIcon,
    Button,
    UserSearch,
    Dropdown,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    entity: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      showUserSearch: false,
      searchQuery: '',
      errorMessage: '',
    }
  },
  computed: {
    entityName() {
      return this.entity?.name
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
        if (!value) {
          this.errorMessage = ''
        }
      },
    },
  },
  updated() {
    this.$resources.sharedWith.fetch()
  },
  mounted() {
    this.$resources.sharedWith.fetch()
    const targetElement = this.$refs.dialogContent?.closest('.overflow-hidden')
    if (targetElement) {
      targetElement.classList.remove('overflow-hidden')
      targetElement.classList.add('self-center')
      targetElement.childNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE)
          node.classList.add('rounded-lg')
      })
    }
  },
  resources: {
    sharedWith() {
      return {
        method: 'drive.api.permissions.get_shared_with_list',
        params: {
          entity_name: this.entityName,
        },
      }
    },
    share() {
      return {
        method: 'drive.api.files.call_controller_method',
        params: {
          method: 'share',
          entity_name: this.entityName,
          user: this.searchQuery,
          write: 1,
        },
        validate(params) {
          if (!params?.user) {
            return 'No user was specified'
          }
        },
        onSuccess(data) {
          this.$resources.share.error = null
          this.$resources.sharedWith.fetch()
          this.showUserSearch = false
          this.searchQuery = ''
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join('\n')
          } else {
            this.errorMessage = error.message
          }
        },
      }
    },
  },
}
</script>
