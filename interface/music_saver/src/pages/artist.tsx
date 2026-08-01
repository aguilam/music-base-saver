import Cover from "~/shared/ui/cover";
import { useParams } from "@solidjs/router";
import AlbumCard from "~/entities/album/ui/albumCard";
import { For, Show } from "solid-js";
import { createArtistQuery } from "~/entities/artists/api/queries";

const ArtistPage = () => {
  const params = useParams()
  const artistQuery = createArtistQuery(() => Number(params.id));
  return (
    <Show when={artistQuery.data} fallback={artistQuery.isLoading ? <div>Loading</div> : <div>Not found</div>}>
      {(artist) => (
        <div>
          <div class="h-48 flex gap-5">
            <Cover coverUri={artist().coverUri} type="artist" size="md" />
            <div class="flex flex-col h-full py-5">
                <p class=" text-secondary-text">Artist</p>
                <p class=" text-5xl font-bold">{artist().name}</p>
            </div>
          </div>
          {artist().albums && (
            <div>
              <p class=" text-2xl font-semibold mb-4">Albums</p>
              <div class="flex gap-5">
                <For each={artist().albums}>
                    {(album) => <AlbumCard content={album} />}
                </For>
              </div>
            </div>
          )}
        </div>
      )}
    </Show>

  );
};

export default ArtistPage;