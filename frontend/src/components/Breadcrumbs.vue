<template>
  <div class="flex items-center text-base">
    <router-link
      v-for="(item, index) in breadcrumbLinks"
      :key="item.label"
      v-slot="{ href, navigate }"
      class="text-xl font-medium"
      :class="isLastItem(index) ? 'text-inherit' : 'text-gray-600'"
      :to="item.route">
      <a v-if="documentRoute(item)" :href="href" @click="navigate">
        {{ item.label }}
        <span v-if="!isLastItem(index)" class="px-2">{{ ">" }}</span>
      </a>
      <input
        v-else="documentRoute(item)"
        v-model="title"
        :placeholder="item.label"
        class="text-xl font-semibold focus:outline-0 focus:form-input focus:text-xl border-gray-400 placeholder-gray-500"
        @input="$resources.updateDocumentTitle.submit()" />
    </router-link>
  </div>
</template>
<script>
export default {
  name: "Breadcrumbs",
  data() {
    return {
      title: "",
      oldTitle: "",
    };
  },
  props: {
    breadcrumbLinks: {
      type: Array,
      required: true,
    },
  },
  computed: {
    titleVal() {
      return this.title ? this.title : this.oldTitle;
    },
    currentTitle() {
      return this.breadcrumbLinks[this.breadcrumbLinks.length - 1].label;
    },
    currentRoute() {
      return this.breadcrumbLinks[this.breadcrumbLinks.length - 1].route;
    },
    currentEntityName() {
      return this.currentRoute.split("/")[2];
    },
  },
  updated() {
    this.title = this.currentTitle;
    this.oldTitle = this.currentTitle;
  },
  methods: {
    documentRoute(item) {
      return !item.route.startsWith("/document");
    },
    isLastItem(index) {
      return index === this.breadcrumbLinks.length - 1;
    },
  },
  resources: {
    /*     updateDocumentTitle() {
      return {
        url: "drive.api.files.rename_doc_entity",
        debounce: 250,
        params: {
          entity_name: this.currentEntityName,
          title: this.titleVal,
        },
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    }, */
    updateDocumentTitle() {
      return {
        url: "drive.api.files.call_controller_method",
        debounce: 250,
        params: {
          method: "rename",
          entity_name: this.currentEntityName,
          new_title: this.titleVal,
        },
        validate(params) {
          if (!params?.new_title) {
            return "New name is required";
          }
        },
        onSuccess(data) {
          this.newName = "";
          this.errorMessage = "";
          this.$emit("success", data);
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
      };
    },
  },
};
</script>
