import { useAlbum } from "@/shared/api/hooks/albums";
import { useParams } from "@solidjs/router";
import { For } from "solid-js";
import { formatTimeToString } from "~/shared/lib/utils";
import Cover from "~/shared/ui/cover";
import TrackCard from "~/entities/track/ui/trackCard";
const AlbumPage = () => {
    const params = useParams()
  const { data: albumInfo, isLoading } = useAlbum(params.id);
  if (isLoading) {
    return <div>Loading</div>;
  }
  return (
    <div>
      <div class="h-48 flex gap-5">
        <Cover coverUri={albumInfo?.coverUri} type="album" size="md" />
        <div class="flex flex-col justify-between h-full py-5">
          <div>
            <p class=" text-slate-400">Album</p>
            <p class=" text-5xl font-bold">{albumInfo?.title}</p>
            <div class="flex gap-1 text-secondary-text">
              <p>{albumInfo?.artist}</p>
              <p>{albumInfo?.year}</p>
              <p>{albumInfo?.trackCount} tracks</p>
              <p>{formatTimeToString(albumInfo?.albumLength ?? 0)}</p>
            </div>
          </div>
        </div>
      </div>
        <div class="">
            <For each={albumInfo?.tracks}>
                {(track) => <TrackCard content={track} isAvatarHidden={true}/>}
            </For>
        </div>
    </div>
  );
};

export default AlbumPage;