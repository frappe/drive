<template>
  <div
    class="flex flex-col items-center justify-start h-full w-full p-2 overflow-hidden">
    <div id="renderContainer" class="object-contain h-[90vh]">
      <FileRender v-if="file.data" :preview-entity="file.data" />
    </div>
    <!--   <div class="flex items-center justify-between mt-2 h-16 w-16">
      <Button v-if="prevEntity?.name" :variant="'ghost'" icon="arrow-left" @click="scrollEntity(true)"></Button>
      <Button v-if="nextEntity?.name" :variant="'ghost'" icon="arrow-right" @click="scrollEntity()"></Button>
    </div> -->
  </div>
</template>

<script setup>
import { useStore } from "vuex";
import { ref, computed, onMounted, defineProps, onBeforeUnmount } from "vue";
import { Button } from "frappe-ui";
import FileRender from "@/components/FileRender.vue";
import { createResource } from "frappe-ui";
import { formatSize, formatDate } from "@/utils/format";
import { useRouter } from "vue-router";

const router = useRouter();
const store = useStore();
const props = defineProps({
  entityName: {
    type: String,
    default: null,
  },
});

onMounted(() => {
  fetchFile(props.entityName);
});

const entity = ref(null);
const currentEntity = ref(props.entityName);
const userId = computed(() => {
  return store.state.auth.user_id;
});

const filteredEntities = computed(() => {
  return store.state.currentViewEntites.filter(
    (item) => item.is_group === 0 || !item.document
  );
});

const currentEntityIndex = computed(() => {
  return filteredEntities.value.findIndex(
    (item) => item.name === props.entityName
  );
});

const prevEntity = computed(() => {
  return filteredEntities.value[currentEntityIndex.value - 1];
});

const nextEntity = computed(() => {
  return filteredEntities.value[currentEntityIndex.value + 1];
});

function fetchFile(currentEntity) {
  file.fetch({ entity_name: currentEntity }).then(() => {
    router.push({
      name: "File",
      params: { entityName: currentEntity },
    });
  });
}

let file = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
  method: "GET",
  params: { entity_name: props.entityName },
  transform(data) {
    entity.value = data;
    data.size_in_bytes = data.file_size;
    data.file_size = formatSize(data.file_size);
    data.modified = formatDate(data.modified);
    data.creation = formatDate(data.creation);
    data.owner = data.owner === userId.value ? "Me" : data.owner;
    store.commit("setEntityInfo", [data]);
  },
  onSuccess(data) {
    let currentBreadcrumbs = [];
    currentBreadcrumbs = store.state.currentBreadcrumbs;

    if (
      !currentBreadcrumbs[currentBreadcrumbs.length - 1].route.includes("/file")
    ) {
      currentBreadcrumbs.push({
        label: data.title,
        route: `/file/${props.entityName}`,
      });
      store.breadcrumbs = currentBreadcrumbs;
      store.commit("setCurrentBreadcrumbs", currentBreadcrumbs);
    }
  },
  onError(error) {
    console.log(error);
  },
});

function scrollEntity(negative = false) {
  currentEntity.value = negative ? prevEntity.value : nextEntity.value;
  fetchFile(currentEntity.value.name);
}

onBeforeUnmount(() => {
  store.commit("setEntityInfo", []);
});
</script>
/**/
