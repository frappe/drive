<template>
  <div class="flex items-center mb-4 ps-1">
    <h1 class="font-semibold text-ink-gray-9">
      {{ __("Storage") }}
    </h1>
    <Button
      :label="__('Sync')"
      class="ml-auto mr-4"
      @click="confirmSync"
    />
  </div>
  <div class="overflow-y-auto ps-1">
    <LoadingIndicator
      v-if="getDiskSettings.loading"
      class="size-5 mx-auto my-10"
    />
    <div
      v-else
      class="flex flex-col gap-4 pb-5 pr-5"
    >
      <FormControl
        v-model="generalSettings.root_folder"
        :label="__('Root Folder Name')"
        placeholder="/"
        :description="__('Where to store Drive files, defaults to the root folder.')"
      />
      <FormControl
        v-model="generalSettings.team_prefix"
        type="select"
        :label="__('Team Prefix')"
        :options="[
          { label: __('Team ID'), value: 'team_id' },
          { label: __('Team Name'), value: 'team_name' },
          { label: __('None'), value: 'none' },
        ]"
        :description="__('The folder name for each team, defaults to the team name.')"
      />

      <FormControl
        v-model="generalSettings.backend_type"
        type="select"
        :label="__('Backend Type')"
        :options="[
          { label: __('Disk'), value: 'disk' },
          { label: __('S3'), value: 's3' },
        ]"
        :description="__('Whether to store on disk or on an S3 bucket.')"
      />
      <div
        v-if="generalSettings.backend_type === 's3'"
        class="flex flex-col gap-4 mt-2"
      >
        <h3 class="font-semibold text-md">
          {{ __("S3 Settings") }}
        </h3>
        <FormControl
          v-model="s3Settings.aws_key"
          :label="__('AWS Key')"
          required
          :placeholder="__('Enter AWS Key')"
        />
        <FormControl
          v-model="s3Settings.aws_secret"
          :label="__('AWS Secret')"
          required
          :placeholder="__('Enter AWS Secret')"
          :description="__('This is not shown after you submit it.')"
          type="password"
        />
        <FormControl
          v-model="s3Settings.bucket"
          required
          :label="__('S3 Bucket')"
          placeholder="bucket.example"
        />
        <FormControl
          v-model="s3Settings.endpoint_url"
          :label="__('Endpoint URL')"
          :placeholder="__('Enter Endpoint URL')"
          :description="__('Optional, only if using a custom endpoint.')"
        />
        <FormControl
          v-model="s3Settings.signature_version"
          :label="__('Signature Version')"
          placeholder="s3v4"
          :description="__('Optional. Some providers only support s3.')"
        />
      </div>
      <Button
        :label="__('Update')"
        variant="solid"
        :disabled="!edited"
        :loading="updateSettings.isLoading"
        class="mt-4"
        @click="updateSettings.submit()"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, markRaw } from "vue"
import {
  FormControl,
  Button,
  createResource,
  LoadingIndicator,
} from "frappe-ui"
import { toast } from "@/utils/toasts"
import { createDialog } from "@/utils/dialogs"
import { getDiskSettings } from "@/resources/permissions"
import SyncBreakdown from "@/components/SyncBreakdown.vue"

const edited = ref(false)

const generalSettings = reactive({
  team_prefix: "team_id",
  root_folder: "",
  backend_type: "disk",
})
const s3Settings = reactive({
  aws_key: "",
  aws_secret: "",
  bucket: "",
  endpoint_url: "",
  signature_version: "",
})

let count = 0
watch(
  [generalSettings, s3Settings],
  () => {
    if (count > 0) edited.value = true
    else count++
  },
  {
    deep: true,
  }
)

function confirmSync() {
  createDialog({
    title: __("Sync files from S3"),
    component: markRaw(SyncBreakdown),
  })
}

getDiskSettings.fetch(null, {
  onSuccess: (data) => {
    delete data.aws_secret
    for (const [key, value] of Object.entries(data)) {
      if (key in generalSettings) generalSettings[key] = value
      if (key in s3Settings) s3Settings[key] = value
    }
    generalSettings.backend_type = data.enabled ? "s3" : "disk"
  },
})

const updateSettings = createResource({
  url: "drive.api.product.disk_settings",
  method: "PUT",
  makeParams: () => ({ ...generalSettings, ...s3Settings }),
  onSuccess() {
    edited.value = false
    toast({
      title: __("S3 settings updated successfully"),
    })
  },
})
</script>
