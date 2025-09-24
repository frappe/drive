<template>
  <div class="flex items-center mb-4 ps-1">
    <h1 class="font-semibold text-ink-gray-9">
      {{ __("S3 Integration") }}
    </h1>
    <Button
      label="Sync"
      @click="confirmSync"
      class="ml-auto mr-4"
    />
  </div>
  <div class="overflow-y-auto ps-1">
    <LoadingIndicator
      class="size-5 mx-auto my-10"
      v-if="getDiskSettings.loading"
    />
    <div
      v-else
      class="flex flex-col gap-4 pb-5 pr-5"
    >
      <FormControl
        label="Root Folder Name"
        placeholder="/"
        v-model="generalSettings.root_folder"
        description="Where to store Drive files, defaults to the root folder."
      />
      <FormControl
        type="select"
        label="Team Prefix"
        :options="[
          { label: 'Team ID', value: 'team_id' },
          { label: 'Team Name', value: 'team_name' },
          { label: 'None', value: 'none' },
        ]"
        v-model="generalSettings.team_prefix"
        description="The folder name for each team, defaults to the team name."
      />

      <FormControl
        type="select"
        label="Backend Type"
        :options="[
          { label: 'Disk', value: 'disk' },
          { label: 'S3', value: 's3' },
        ]"
        v-model="generalSettings.backend_type"
        description="Whether to store on disk or on an S3 bucket."
      />
      <div
        v-if="generalSettings.backend_type === 's3'"
        class="flex flex-col gap-4 mt-2"
      >
        <h3 class="font-semibold text-md">S3 Settings</h3>
        <FormControl
          label="AWS Key"
          required
          placeholder="Enter AWS Key"
          v-model="s3Settings.aws_key"
        />
        <FormControl
          label="AWS Secret"
          required
          placeholder="Enter AWS Secret"
          v-model="s3Settings.aws_secret"
          description="This isn't shown after you submit it."
          type="password"
        />
        <FormControl
          required
          label="S3 Bucket"
          placeholder="bucket.example"
          v-model="s3Settings.bucket"
        />
        <FormControl
          label="Endpoint URL"
          placeholder="Enter Endpoint URL"
          v-model="s3Settings.endpoint_url"
          description="Optional, only if using a custom endpoint."
        />
        <FormControl
          label="Signature Version"
          placeholder="s3v4"
          v-model="s3Settings.signature_version"
          description="Optional. Some providers only support 's3'."
        />
      </div>
      <Button
        label="Update"
        variant="solid"
        :disabled="!edited"
        :loading="updateSettings.isLoading"
        @click="updateSettings.submit()"
        class="mt-4"
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
    title: "Sync files from S3",
    component: markRaw(SyncBreakdown),
  })
}

getDiskSettings.fetch(null, {
  onSuccess: (data) => {
    delete data.aws_secret
    for (let [key, value] of Object.entries(data)) {
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
      title: "S3 settings updated successfully",
    })
  },
})
</script>
