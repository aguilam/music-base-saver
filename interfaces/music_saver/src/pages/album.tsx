import { useParams } from "@solidjs/router";
import { Show } from "solid-js";
import { formatTimeToString } from "~/shared/lib/utils";
import Cover from "~/shared/ui/cover";
import { createAlbumQuery } from "~/entities/album/api/queries";
import TrackList from "~/entities/track/ui/trackList";
import ArtistsNames from "~/entities/artists/ui/artistsNames";
const AlbumPage = () => {
  
  const params = useParams();
  const albumQuery = createAlbumQuery(() => Number(params.id));

  return (
    <Show
      when={albumQuery.data}
      fallback={albumQuery.isLoading ? <div>Loading</div> : <div>Not found</div>}
    >
      {(album) => (
        <div>
          <div class="h-48 flex gap-5">
            <Cover coverUri={album().coverUri} type="album" size="md" />
            <div class="flex flex-col justify-between h-full py-5">
              <div>
                <p class=" text-slate-400">Album</p>
                <p class=" text-5xl font-bold">{album().title}</p>
                <div class="flex gap-1 text-secondary-text">
                  <ArtistsNames artists={album().artists}/>
                  <p>{album().year}</p>
                  <p>{album().tracksCount} tracks</p>
                  <p>{formatTimeToString(album().duration ?? 0)}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="">
            <TrackList tracks={album().tracks} />
          </div>
        </div>
      )}
    </Show>
  );
};

export default AlbumPage;
