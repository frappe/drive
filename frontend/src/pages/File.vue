<template>
  <div
    class="h-full w-full overflow-hidden flex flex-col items-center justify-start">
    <div
      :draggable="false"
      id="renderContainer"
      class="flex items-center justify-center h-full w-full min-h-[85vh] max-h-[85vh] mt-3">
      <FileRender v-if="file.data" :preview-entity="file.data" />
    </div>
    <div
      v-show="filteredEntities.length > 1"
      class="absolute bottom-[-1%] left-[50%] center-transform flex items-center justify-center p-1 gap-1 h-10 rounded-lg shadow-xl bg-white">
      <Button
        :disabled="!prevEntity?.name"
        :variant="'ghost'"
        icon="arrow-left"
        @click="scrollEntity(true)"></Button>
      <Button @click="enterFullScreen" :variant="'ghost'">
        <Scan class="w-4" />
      </Button>
      <!--  <Button :variant="'ghost'">
      <FileSignature class="w-4"/>
    </Button> -->
      <Button
        :disabled="!nextEntity?.name"
        :variant="'ghost'"
        icon="arrow-right"
        @click="scrollEntity()"></Button>
    </div>
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
import { Scan, FileSignature } from "lucide-vue-next";
import { onKeyStroke } from "@vueuse/core";

const router = useRouter();
const store = useStore();
const props = defineProps({
  entityName: {
    type: String,
    default: null,
  },
});

const entity = ref(null);
const currentEntity = ref(props.entityName);
const userId = computed(() => {
  return store.state.auth.user_id;
});

const filteredEntities = computed(() => {
  return store.state.currentViewEntites.filter(
    (item) => item.is_group === 0 && item.mime_type !== "frappe_doc"
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
    router.replace({
      name: "File",
      params: { entityName: currentEntity },
    });
  });
}

function enterFullScreen(id) {
  let elem = document.getElementById("renderContainer");
  if (elem.requestFullscreen) {
    elem.requestFullscreen();
  } else if (elem.mozRequestFullScreen) {
    /* Firefox */
    elem.mozRequestFullScreen();
  } else if (elem.webkitRequestFullscreen) {
    /* Chrome, Safari & Opera */
    elem.webkitRequestFullscreen();
  } else if (elem.msRequestFullscreen) {
    /* IE/Edge */
    elem.msRequestFullscreen();
  }
}

onKeyStroke("ArrowLeft", (e) => {
  e.preventDefault();
  scrollEntity(true);
});

onKeyStroke("ArrowRight", (e) => {
  e.preventDefault();
  scrollEntity();
});

let file = createResource({
  url: "drive.api.permissions.get_entity_with_permissions",
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
    } else {
      let scrolledFileBreadcrumb = {
        label: data.title,
        route: `/file/${data.name}`,
      };
      currentBreadcrumbs.splice(
        currentBreadcrumbs.length - 1,
        1,
        scrolledFileBreadcrumb
      );
    }
  },
  onError(error) {
    if (error && error.exc_type === "PermissionError") {
      store.commit("setError", {
        iconName: "alert-triangle",
        iconClass: "fill-amber-500 stroke-white",
        primaryMessage: "Forbidden",
        secondaryMessage: "Insufficient permissions for this resource",
      });
    }
    router.replace({ name: "Error" });
  },
});

function scrollEntity(negative = false) {
  currentEntity.value = negative ? prevEntity.value : nextEntity.value;
  fetchFile(currentEntity.value.name);
}

onMounted(() => {
  fetchFile(props.entityName);
});

onBeforeUnmount(() => {
  store.commit("setEntityInfo", []);
});
</script>

<style scoped>
.center-transform {
  transform: translate(-50%, -50%);
}

#renderContainer::backdrop {
  background-color: rgb(0, 0, 0);
  min-width: 100vw;
  min-height: 100vh;
  position: fixed;
  width: 100%;
  height: 100%;
  left: 0;
  top: 0;
}
</style>
