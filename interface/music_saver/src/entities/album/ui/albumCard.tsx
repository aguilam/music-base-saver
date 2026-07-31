import { A } from "@solidjs/router";
import Cover from "../../../shared/ui/cover";
import { ShortAlbum } from "../model/types";

interface AlbumCardProps {
  content: ShortAlbum;
}

const AlbumCard = (props: AlbumCardProps) => {
  const album = props.content;
  return (
    <A href={`/album/${album.id}`}>
      <div class="w-56 ring-0 bg-transparent">
        <Cover coverUri={album.coverUri} type="album" size="lg" />
        <p class="text-primary-text mt-2">{album.title}</p>
        <p class="text-secondary-text">
          {album.artists[0].name} {album.year ? `- ${album.year}` : ""}
        </p>
      </div>
    </A>
  );
};

export default AlbumCard;