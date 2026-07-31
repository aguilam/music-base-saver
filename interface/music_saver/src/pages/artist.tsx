import { useArtist } from "@/shared/api/hooks/artists";
import Cover from "~/shared/ui/cover";
import { useParams } from "@solidjs/router";
import AlbumCard from "~/entities/album/ui/albumCard";
import { For } from "solid-js";

const ArtistPage = () => {
    const params = useParams()
  const { data: artistInfo, isLoading } = useArtist(params.id);
  if (isLoading) {
    return <div>Loading</div>;
  }
  return (
    <div>
      <div class="h-48 flex gap-5">
        <Cover coverUri={artistInfo?.avatarUri} type="artist" size="md" />
        <div class="flex flex-col h-full py-5">
            <p class=" text-secondary-text">Artist</p>
            <p class=" text-5xl font-bold">{artistInfo?.name}</p>
        </div>
      </div>
      {artistInfo?.albums && (
        <div>
          <p class=" text-2xl font-semibold mb-4">Albums</p>
          <div class="flex gap-5">
            <For each={artistInfo?.albums}>
                {(album) => <AlbumCard content={album} />}
            </For>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArtistPage;