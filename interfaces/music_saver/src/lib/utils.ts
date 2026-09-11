import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { onCleanup, createEffect, Accessor } from "solid-js";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function createObserver(target: Accessor<HTMLElement | undefined>, onIntersect: () => void) {
  createEffect(() => {
    const el = target();
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        console.log(entry);
        if (entry.isIntersecting) {
          onIntersect();
        }
      },
      { rootMargin: "240px" },
    );

    observer.observe(el);
    onCleanup(() => observer.disconnect());
  });
}
