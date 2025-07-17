import { reactive, ref } from "vue"
import { Dialog, ErrorMessage, Button, type ButtonProps } from "frappe-ui"

type DialogActionContext = {
  close: () => void
}
type DialogAction = ButtonProps & {
  onClick?: (context: DialogActionContext) => void | Promise<void>
}

interface DialogOptions {
  title?: string
  message?: string
  size?:
    | "xs"
    | "sm"
    | "md"
    | "lg"
    | "xl"
    | "2xl"
    | "3xl"
    | "4xl"
    | "5xl"
    | "6xl"
    | "7xl"
  actions?: Array<DialogAction>
  position?: "top" | "center"
  show: boolean
  key?: string
  error?: string
}

type UserDialogOptions = Omit<DialogOptions, "show" | "key">

let dialogs = ref<Array<DialogOptions>>([])

export let Dialogs = {
  name: "Dialogs",
  render() {
    return dialogs.value.map((dialog) => (
      <Dialog
        options={dialog}
        modelValue={dialog.show}
        onUpdate:modelValue={(val) => (dialog.show = val)}
      >
        {{
          "body-content": () => {
            return [
              dialog.message && (
                <p class="text-p-base text-ink-gray-6">{dialog.message}</p>
              ),
              <ErrorMessage
                class="mt-2"
                message={dialog.error}
              />,
            ]
          },
          actions: ({ close }) => {
            let fullWidth = dialog.actions?.length === 1
            return (
              <div class="flex justify-end gap-2">
                {dialog.actions?.map((action) => {
                  return (
                    <Button
                      key={action.label}
                      {...buttonProps(action, close)}
                      class={fullWidth ? "w-full" : ""}
                    >
                      {action.label}
                    </Button>
                  )
                })}
              </div>
            )
          },
        }}
      </Dialog>
    ))
  },
}

function buttonProps(action: DialogAction, close: () => void): ButtonProps {
  let _action = reactive({
    ...action,
    loading: false,
    onClick: !action.onClick
      ? close
      : async () => {
          _action.loading = true
          try {
            if (action.onClick) {
              await action.onClick({ close })
            }
          } finally {
            _action.loading = false
          }
        },
  })

  return _action
}

export function createDialog(userDialogOptions: UserDialogOptions) {
  let dialog = reactive<DialogOptions>({
    ...userDialogOptions,
    show: false,
    key: "dialog-" + dialogs.value.length,
  })

  setTimeout(() => {
    dialog.show = true
  }, 0)
  dialogs.value.push(dialog)
  return dialog
}
