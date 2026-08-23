import { createMemo, For, Show } from "solid-js"
import { createTracksQuery } from "~/entities/track"
import TrackCard from "~/entities/track/ui/trackCard"
import { createObserver } from "~/lib/utils"

const TracksPage = () => {
    const query = createTracksQuery()
    let loaderRef: HTMLDivElement | undefined

    const tracks = createMemo(() => 
      query.data?.pages.flatMap((page) => page.items) ?? []
    )
    createObserver(
        () => loaderRef,
        () => {
            if (query.hasNextPage && !query.isFetchingNextPage) {
                query.fetchNextPage()
            }
        }
    )
    return (
        <div>
            <div class="grid grid-cols-[repeat(auto-fill,minmax(360px,1fr))] gap-4">
                <For each={tracks()}>
                    {(item) => <TrackCard content={item}/>}
                </For>
            </div>
            <Show when={query.hasNextPage}>
                <div ref={loaderRef} class="h-20 flex items-center justify-center">
                  <p class="text-neutral-400">Загрузка...</p>
                </div>
            </Show>
        </div>
    )
}
export default TracksPage