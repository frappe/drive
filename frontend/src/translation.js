import { createResource } from "frappe-ui"

export default function translationPlugin(app) {
  app.config.globalProperties.__ = translate
  window.__ = translate
  fetchTranslations()
}

function translate(message) {
  let translatedMessages = window.translatedMessages || {}
  let translatedMessage = translatedMessages[message] || message

  const hasPlaceholders = /{\d+}/.test(message)
  if (!hasPlaceholders) {
    return translatedMessage
  }
  return {
    format: function (...args) {
      return translatedMessage.replace(/{(\d+)}/g, function (match, number) {
        return typeof args[number] != "undefined" ? args[number] : match
      })
    },
  }
}

function fetchTranslations() {
  createResource({
    url: "drive.api.product.get_translations",
    cache: ["translations", Date.now()], // Add timestamp to prevent caching
    auto: true,
    transform: (data) => {
      console.log("Loaded translations:", data)
      console.log("Number of translations:", Object.keys(data || {}).length)
      window.translatedMessages = data || {}
      
      // Test a few translations immediately
      const testKeys = ["Home", "Search", "Settings"];
      testKeys.forEach(key => {
        if (window.translatedMessages[key]) {
          console.log(`✓ ${key} -> ${window.translatedMessages[key]}`);
        } else {
          console.log(`✗ ${key} not found`);
        }
      });
      
      return data
    },
    onError: (error) => {
      console.error("Translation fetch error:", error)
      window.translatedMessages = {}
    }
  })
}
