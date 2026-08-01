import { useParams } from "@solidjs/router";
import { For, Show } from "solid-js";
import Cover from "~/shared/ui/cover";
import TrackCard from "~/entities/track/ui/trackCard";
import { createPlaylistQuery } from "~/entities/playlist/api/queries";

const PlaylistPage = () => {
  const params = useParams()
  const playlistQuery = createPlaylistQuery(() => Number(params.id));
  return (
    <Show when={playlistQuery.data} fallback={playlistQuery.isLoading ? <div>Loading</div> : <div>Not found</div>}>
      {(playlist) => (
        <div>
          <div class="h-48 flex gap-5">
            <Cover coverUri={playlist().coverUri} type="playlist" size="md" />
            <div class="flex flex-col justify-between h-full py-5">
              <div>
                <p class=" text-secondary-text">Playlist</p>
                <p class=" text-5xl font-bold text-primary-text">
                  {playlist().title}
                </p>
              </div>
            </div>
          </div>
          {playlist().tracks && (
            <div class="gap-5">
                <For each={playlist().tracks}>
                    {(track) => <TrackCard content={track} />}
                </For>
            </div>
          )}
        </div>
      )}
    </Show>
  );
};

export default PlaylistPage;