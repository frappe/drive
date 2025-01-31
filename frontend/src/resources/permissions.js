import { createResource } from "frappe-ui"

export const getUsersWithAccess = createResource({
  url: "drive.api.permissions.get_shared_with_list",
  makeParams: (params) => params,
})

export const updateAccess = createResource({
  url: "drive.api.files.call_controller_method",
  makeParams: (params) => ({ ...params, method: params.method || "share" }),
})
