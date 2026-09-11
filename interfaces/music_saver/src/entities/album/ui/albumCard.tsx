import { A } from "@solidjs/router";
import Cover from "../../../shared/ui/cover";
import { ShortAlbum } from "../model/types";
import ArtistsNames from "~/entities/artists/ui/artistsNames";
import { JSX, splitProps } from "solid-js";

interface AlbumCardProps extends JSX.HTMLAttributes<HTMLDivElement> {
  content: ShortAlbum;
}

const AlbumCard = (props: AlbumCardProps) => {
  const [local, rest] = splitProps(props, ["content"]);
  const album = () => local.content;
  return (
    <A href={`/album/${album().id}`}>
      <div class="w-56 ring-0 bg-transparent" {...rest}>
        <Cover coverUri={album().coverUri} type="album" size="lg" />
        <p class="text-primary-text mt-2">{album().title}</p>
        <p class="text-secondary-text">
          <ArtistsNames artists={album().artists} /> {album().year ? `- ${album().year}` : ""}
        </p>
      </div>
    </A>
  );
};

export default AlbumCard;
