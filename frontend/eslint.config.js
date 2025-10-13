import pluginVue from "eslint-plugin-vue"
import unusedImports from "eslint-plugin-unused-imports"
import {
  defineConfigWithVueTs,
  vueTsConfigs,
} from "@vue/eslint-config-typescript"

export default defineConfigWithVueTs([
  // js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  vueTsConfigs.recommended,
  {
    files: ["*.vue"],
  },
  {
    plugins: {
      "unused-imports": unusedImports,
    },
    rules: {
      "unused-imports/no-unused-imports": "error",
      "vue/require-default-prop": "off",
      "vue/multi-word-component-names": "off",
      "vue/no-reserved-component-names": "off",
      "vue/block-lang": "off",
      "vue/no-side-effects-in-computed-properties": "off",
      "vue/no-mutating-props": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
    languageOptions: {
      sourceType: "module",
      // globals: {
      //   ...globals.browser,
      // },
    },
  },
])
