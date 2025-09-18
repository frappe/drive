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
      v-if="getSettings.loading || getSettings.error"
      class="size-5 mx-auto my-10"
    />
    <div
      v-else
      class="flex flex-col gap-4 pb-5 pr-5"
    >
      <FormControl
        type="select"
        label="Root Folder Type"
        :options="[
          { label: 'Team ID', value: 'team_id' },
          { label: 'Team Name', value: 'team_name' },
          { label: 'Other', value: 'other' },
        ]"
        v-model="generalSettings.team_prefix"
        description="The root folder name for each team, defaults to team ID."
      />
      <FormControl
        v-if="generalSettings.team_prefix === 'other'"
        label="Root Folder Name"
        placeholder="team"
        v-model="generalSettings.root_folder"
        description="Value to use for the root folder. Use / to not use a separate folder."
      />
      <FormControl
        type="select"
        label="Backend Type"
        :options="[
          { label: 'Disk', value: 'disk' },
          { label: 'S3', value: 's3' },
        ]"
        v-model="generalSettings.backend_type"
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
import { ref, reactive, watch, h } from "vue"
import {
  FormControl,
  Button,
  createResource,
  LoadingIndicator,
} from "frappe-ui"
import { useRoute } from "vue-router"
import { toast } from "@/utils/toasts"
import { createDialog } from "@/utils/dialogs"
import SyncBreakdown from "@/components/SyncBreakdown.vue"

const route = useRoute()

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
    component: h(SyncBreakdown, { team: route.params.team }),
  })
}

const getSettings = createResource({
  url: "drive.api.product.disk_settings",
  method: "GET",
  onSuccess: (data) => {
    delete data.aws_secret
    for (let [key, value] of Object.entries(data)) {
      if (key in generalSettings) generalSettings[key] = value
      if (key in s3Settings) s3Settings[key] = value
    }
    generalSettings.backend_type = data.enabled ? "s3" : "disk"
  },
})
getSettings.fetch()

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
