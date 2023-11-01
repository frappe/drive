import { toast } from "../utils/toasts.js";

export async function getLink(entity) {
  const link = entity.is_group
    ? `${window.location.origin}/drive/folder/${entity.name}`
    : entity.document
    ? `${window.location.origin}/drive/document/${entity.name}`
    : `${window.location.origin}/drive/file/${entity.name}`;
  await navigator.clipboard.writeText(link);
  toast({
    title: "Copied link!",
    position: "bottom-right",
    timeout: 2,
  });
}
