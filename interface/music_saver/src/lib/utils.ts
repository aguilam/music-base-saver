import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { onMount, onCleanup } from "solid-js"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function createObserver(
  target: () => HTMLElement | undefined,
  onIntersect: () => void
) {
  onMount(() => {
    const el = target()
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onIntersect()
        }
      },
      { rootMargin: "230px" }
    )

    observer.observe(el)
    onCleanup(() => observer.disconnect())
  })
}