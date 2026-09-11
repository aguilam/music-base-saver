import { createMemo, createSignal, For, Show } from "solid-js";
import { createArtistsQuery } from "~/entities/artists/api/queries";
import ArtistCard from "~/entities/artists/ui/artistCard";
import { createObserver } from "~/lib/utils";

const ArtistsPage = () => {
  const query = createArtistsQuery();
  const [loaderRef, setLoaderRef] = createSignal<HTMLDivElement | undefined>(undefined);
  const artists = createMemo(() => query.data?.pages.flatMap((page) => page.items) ?? []);
  createObserver(
    () => loaderRef(),
    () => {
      if (query.hasNextPage && !query.isFetchingNextPage) {
        query.fetchNextPage();
      }
    },
  );
  return (
    <div>
      <div class="grid grid-cols-[repeat(auto-fill,minmax(224px,1fr))] gap-4">
        <For each={artists()}>
          {(item, index) => (
            <ArtistCard
              content={item}
              ref={(ref) => (index() === artists().length - 1 ? setLoaderRef(ref) : undefined)}
            />
          )}
        </For>
      </div>
      <Show when={query.hasNextPage}>
        <div ref={(ref) => setLoaderRef(ref)} class="h-20 flex items-center justify-center">
          <p class="text-neutral-400">Загрузка...</p>
        </div>
      </Show>
    </div>
  );
};
export default ArtistsPage;
