import { createResource } from "frappe-ui"
import router from "@/router.js"

export const getUsersWithAccess = createResource({
  url: "drive.api.permissions.get_shared_with_list",
  makeParams: (params) => params,
})

export const updateAccess = createResource({
  url: "drive.api.files.call_controller_method",
  makeParams: (params) => ({ ...params, method: params.method || "share" }),
})

export const notifCount = createResource({
  url: "/api/method/drive.api.notifications.get_unread_count",
  method: "GET",
  cache: "notif-count",
})

export const generalAccess = createResource({
  url: "drive.api.permissions.get_user_access",
  auto: false,
})

export const userList = createResource({
  url: "drive.api.permissions.get_shared_with_list",
  auto: false,
})

export const allUsers = createResource({
  url: "drive.utils.users.get_all_users",
  method: "GET",
  transform: (data) => {
    data.map((item) => {
      item.value = item.email
      item.label = item.full_name.trimEnd()
    })
  },
})
