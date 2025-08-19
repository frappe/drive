import store from "@/store"

export const manageBreadcrumbs = (to) => {
  if (
    store.state.breadcrumbs[store.state.breadcrumbs.length - 1]?.name !==
    to.params.entityName
  ) {
    store.state.breadcrumbs.splice(1)
    store.state.breadcrumbs.push({ loading: true })
  }
}
