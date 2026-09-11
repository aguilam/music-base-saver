import { A } from "@solidjs/router";
import Cover from "../../../shared/ui/cover";
import { ShortArtist } from "../model/types";
import { JSX, splitProps } from "solid-js";

interface PlaylistCardProps extends JSX.HTMLAttributes<HTMLDivElement> {
  content: ShortArtist;
}

const ArtistCard = (props: PlaylistCardProps) => {
  const [local, rest] = splitProps(props, ["content"]);

  return (
    <A href={`/artist/${local.content.id}`}>
      <div class="w-56 p-0 ring-0 bg-transparent" {...rest}>
        <div class="flex flex-col items-center px-0">
          <Cover coverUri={local.content.coverUri} type="artist" size="lg" />
          <p class="text-primary-text mt-2">{local.content.name}</p>
        </div>
      </div>
    </A>
  );
};

export default ArtistCard;
