<template>
  <Dialog :options="{ title: `Share '${entityTitle}'` }" v-model="open" @click="($event) => $event.stopPropagation()">
    <template #body-content>
      <div class="text-left min-w-[16rem]" ref="dialogContent">
        <div class="border rounded-lg py-3 px-4">
          <div class="flex flex-row">
            <div class="flex my-auto">
              <FeatherIcon name="globe" :strokeWidth="2" class="h-5 text-yellow-600" />
            </div>
            <div class="grow ml-4">
              <div class="text-[14px] font-medium text-gray-900">Public access</div>
              <p class="text-base text-gray-700">{{ accessMessage }}</p>
            </div>
            <div class="flex my-auto">
              <Switch v-model="generalAccess.read" :class="generalAccess.read ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-7 items-center rounded-full" @change="$resources.hello">
                <span :class="generalAccess.read ? 'translate-x-4' : 'translate-x-1'"
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>
          <div v-if="generalAccess.read" class="flex flex-row mt-3">
            <div class=" grow text-[14px] text-gray-900">Allow edit</div>
            <div class="flex my-auto">
              <Switch v-model="generalAccess.write" :class="generalAccess.write ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-7 items-center rounded-full" @change="$resources.hello">
                <span :class="generalAccess.write ? 'translate-x-4' : 'translate-x-1'"
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>
          <div v-if="generalAccess.read" class="flex flex-row mt-2">
            <div class=" grow text-[14px] text-gray-900">Allow comments</div>
            <div class="flex my-auto">
              <Switch :class="false ? 'bg-blue-500' : 'bg-gray-200'"
                class="relative inline-flex h-4 w-7 items-center rounded-full" @change="$resources.hello">
                <span :class="false ? 'translate-x-4' : 'translate-x-1'"
                  class="inline-block h-2 w-2 transform rounded-full bg-white transition" />
              </Switch>
            </div>
          </div>
        </div>
        <div class="flex items-start mt-4 gap-2 w-full relative">
          <UserSearch class="flex-1 invisible" />
          <UserSearch v-model="searchQuery" @submit="
            (user) =>
              $resources.share.submit({
                method: 'share',
                entity_name: entityName,
                user: user,
                write: 0,
                share: 1,
              })
          " class="flex-1 absolute w-[calc(100%_-_5.5rem)]" />
          <Button class="focus:ring-0 focus:ring-offset-0 w-20 h-8" appearance="primary"
            @click="$resources.share.fetch()">Invite</Button>
        </div>
        <ErrorMessage v-if="$resources.share.error" class="mt-2" :message="errorMessage" />
        <div class="flex mt-5 text-[14px] text-gray-600">Members</div>
        <div v-for="user in $resources.sharedWith.data" :key="user.user"
          class="mt-3 flex flex-row w-full gap-2 items-center antialiased ">
          <div class="overflow-hidden rounded-full h-9 w-9">
            <img v-if="user.user_image" :src="user.user_image" class="object-cover rounded-full h-7 w-7" />
            <div v-else
              class="flex items-center justify-center w-full h-full text-base text-gray-600 uppercase bg-gray-200">
              {{ user.full_name[0] }}
            </div>
          </div>
          <div class="grow truncate">
            <div class="text-gray-900 text-[14px] font-medium">{{ user.full_name }}</div>
            <div class="text-gray-600 text-base">{{ user.user }}</div>
          </div>
          <Dropdown placement="right" :options="
            [
              { label: 'Viewer' },
              { label: 'Editor' },
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
          ">
            <Button iconRight="chevron-down" :loading="user.loading"
              class="text-sm w-24 focus:ring-0 focus:ring-offset-0 text-gray-700 text-[13px]" appearance="minimal">
              {{ user.write ? 'Editor' : 'Viewer' }}
            </Button>
          </Dropdown>
        </div>
        <div class="flex mt-5">
          <Button icon-left="link" appearance="white" @click="getLink">Copy link</Button>
          <Button appearance="minimal" class="ml-auto text-gray-700 hover:bg-white focus:bg-white active:bg-white"
            iconRight="info">Learn about sharing</Button>
        </div>
        <Alert :title="alertMessage" class="mt-5" v-if="showAlert"></Alert>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, ErrorMessage, FeatherIcon, Button, Dropdown, Alert } from 'frappe-ui'
import { Switch } from '@headlessui/vue'
import UserSearch from '@/components/UserSearch.vue'

export default {
  name: 'ShareDialog',
  components: {
    Dialog,
    ErrorMessage,
    FeatherIcon,
    Button,
    UserSearch,
    Dropdown,
    Alert,
    Switch,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    entityName: {
      type: String,
      required: true,
    },
    entityTitle: {
      type: String,
      required: true,
    },
    isFolder: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['update:modelValue', 'success'],
  data() {
    return {
      generalAccess: {},
      saveLoading: false,
      searchQuery: '',
      errorMessage: '',
      showAlert: false,
      alertMessage: ""
    }
  },
  computed: {
    accessChanged() {
      return JSON.stringify(this.generalAccess) !== JSON.stringify(this.$resources.generalAccess.data)
    },
    accessMessage() {
      if (this.generalAccess.read)
        return this.generalAccess.write ? "Anyone with the link can edit" : "Anyone with the link can view"
      return "Publish and share link with anyone"
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
        if (!value) {
          if (this.accessChanged) {
            this.saveLoading = true
            this.$resources.updateAccess.submit({
              method: 'set_general_access',
              entity_name: this.entityName,
              new_access: this.generalAccess
            })
              .then(() => {
                this.saveLoading = false
              })
          }
          this.errorMessage = ''
        }
      },
    },
  },
  methods: {
    async getLink() {
      this.showAlert = false
      const link = this.isFolder ?
        `${window.location.origin}/drive/shared/folder/${this.entityName}` :
        `${window.location.origin}/drive/file/${this.entityName}`
      try {
        await navigator.clipboard.writeText(link);
        this.alertMessage = "Link copied successfully"
        this.showAlert = true
      } catch ($e) {
        this.alertMessage = "Some error occurred while copying the link"
        this.showAlert = true
      }
    }
  },
  mounted() {
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
        auto: true
      }
    },
    generalAccess() {
      return {
        method: 'drive.api.permissions.get_general_access',
        params: { entity_name: this.entityName, },
        onSuccess(data) {
          data = data || {}
          data.read = !!data.read
          data.write = !!data.write
          this.$resources.generalAccess.data = data
          this.generalAccess = Object.assign({}, data)

        },
        auto: true
      }
    },
    share() {
      return {
        method: 'drive.api.files.call_controller_method',
        params: {
          method: 'share',
          entity_name: this.entityName,
          user: this.searchQuery,
          write: 0,
        },
        validate(params) {
          if (!params?.user) {
            return 'No user was specified'
          }
        },
        onSuccess() {
          this.$resources.share.error = null
          this.$resources.sharedWith.fetch()
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
    updateAccess() {
      return {
        method: 'drive.api.files.call_controller_method',
        onSuccess() {
          this.$resources.generalAccess.fetch()
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
