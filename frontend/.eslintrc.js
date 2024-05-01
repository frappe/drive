module.exports = {
  env: {
    node: true,
  },
  extends: ["eslint:recommended", "plugin:vue/vue3-recommended", "prettier"],
  rules: {
    // override/add rules settings here, such as:
    // 'vue/no-unused-vars': 'error'
    // "vue/require-default-prop": "off",
    // Frappe ui
    "vue/no-reserved-component-names": "off",
    "vue/multi-word-component-names": "off",
  },
}
