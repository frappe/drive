import { computed, unref } from "vue"

export function useTimeAgoVi(time) {
  return computed(() => {
    const timeValue = unref(time)
    if (!timeValue) return ""
    
    const now = new Date()
    const target = new Date(timeValue)
    const diff = now - target
    
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    const weeks = Math.floor(days / 7)
    const months = Math.floor(days / 30)
    const years = Math.floor(days / 365)
    
    if (seconds < 60) {
      return "vừa xong"
    } else if (minutes < 60) {
      return `${minutes} phút trước`
    } else if (hours < 24) {
      return `${hours} giờ trước`
    } else if (days < 7) {
      return `${days} ngày trước`
    } else if (weeks < 4) {
      return `${weeks} tuần trước`
    } else if (months < 12) {
      return `${months} tháng trước`
    } else {
      return `${years} năm trước`
    }
  })
}
