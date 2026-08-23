import { createMemo, For, Show } from "solid-js"
import { createArtistsQuery } from "~/entities/artists/api/queries"
import ArtistCard from "~/entities/artists/ui/artistCard"
import { createObserver } from "~/lib/utils"

const ArtistsPage = () => {
    const query = createArtistsQuery()
    let loaderRef: HTMLDivElement | undefined

    const artists = createMemo(() => 
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
                <For each={artists()}>
                    {(item) => <ArtistCard content={item}/>}
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
export default ArtistsPage