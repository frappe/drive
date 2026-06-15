import { createResource, toast } from 'frappe-ui'
import { openEntity } from './utils'

export const getTeams = createResource({
  url: 'drive.api.permissions.get_teams',
  params: {
    details: 1,
  },
  method: 'GET',
  cache: 'teams',
})

export const move = createResource({
  url: 'drive.api.files.move',
  onSuccess(data) {
    toast.success('Moved to ' + data.file_name, {
      action: {
        label: 'Go to folder',
        onClick: () => openEntity({ name: data.name, is_folder: true }),
      },
    })
  },
  onError() {
    toast.error('Could not move this file.')
  },
})

// Share dialog resources
export const usersWithAccess = createResource({
  url: 'drive.api.permissions.get_shared_with_list',
  makeParams: (params) => params,
})

export const updateAccess = createResource({
  url: 'drive.api.files.update_access',
  makeParams: (params) => ({ ...params, method: params.method || 'share' }),
  onError: (error) => toast.error(error.messages[0]),
})

export const allUsers = createResource({
  url: 'drive.api.product.get_team_users',
  transform: (data) => {
    data.map((item) => {
      item.value = item.email
      item.label = item.full_name.trimEnd()
    })
    return data
  },
})

export const rename = createResource({
  url: 'drive.api.files.rename',
  method: 'POST',
  makeParams: (data) => {
    return {
      ...data,
    }
  },
  onError(error) {
    toast.error(error)
  },
})
