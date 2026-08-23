import { createMemo, For, Show } from "solid-js"
import { createAlbumsQuery } from "~/entities/album"
import AlbumCard from "~/entities/album/ui/albumCard"
import { createObserver } from "~/lib/utils"

const AlbumsPage = () => {
    const query = createAlbumsQuery()
    let loaderRef: HTMLDivElement | undefined

    const albums = createMemo(() => 
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
            <div class="grid grid-cols-[repeat(auto-fill,minmax(224px,1fr))] gap-4">
                <For each={albums()}>
                    {(item) => <AlbumCard content={item}/>}
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
export default AlbumsPage