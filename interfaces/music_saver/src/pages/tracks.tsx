import { createMemo, createSignal, For, Show } from "solid-js";
import { createTracksQuery } from "~/entities/track";
import TrackCard from "~/entities/track/ui/trackCard";
import { createObserver } from "~/lib/utils";

const TracksPage = () => {
  const query = createTracksQuery();
  const [loaderRef, setLoaderRef] = createSignal<HTMLDivElement | undefined>(undefined);

  const tracks = createMemo(() => query.data?.pages.flatMap((page) => page.items) ?? []);
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
      <div class="grid grid-cols-[repeat(auto-fill,minmax(400px,1fr))] gap-4">
        <For each={tracks()}>
          {(item, index) => (
            <TrackCard
              content={item}
              ref={(ref) => (index() === tracks().length - 1 ? setLoaderRef(ref) : undefined)}
            />
          )}
        </For>
      </div>
      <Show when={query.hasNextPage}>
        <div class="h-20 flex items-center justify-center">
          <p class="text-neutral-400">Загрузка...</p>
        </div>
      </Show>
    </div>
  );
};
export default TracksPage;
