export default function getIconUrl(name) {
  return new URL(`/src/assets/images/icons/${name}.svg`, import.meta.url);
}
