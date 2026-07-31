import { usePlaylist } from "@/shared/api/hooks/playlists";
import { useParams } from "@solidjs/router";
import { For } from "solid-js";
import Cover from "~/shared/ui/cover";
import TrackCard from "~/entities/track/ui/trackCard";

const PlaylistPage = () => {
    const params = useParams()
  const { data: playlistInfo, isLoading } = usePlaylist(params.id);
  if (isLoading) {
    return <div>Loading</div>;
  }
  return (
    <div>
      <div class="h-48 flex gap-5">
        <Cover coverUri={playlistInfo?.coverUri} type="playlist" size="md" />
        <div class="flex flex-col justify-between h-full py-5">
          <div>
            <p class=" text-secondary-text">Playlist</p>
            <p class=" text-5xl font-bold text-primary-text">
              {playlistInfo?.title}
            </p>
          </div>
        </div>
      </div>
      {playlistInfo?.tracks && (
        <div class="gap-5">
            <For each={playlistInfo?.tracks}>
                {(track) => <TrackCard content={track} />}
            </For>
        </div>
      )}
    </div>
  );
};

export default PlaylistPage;