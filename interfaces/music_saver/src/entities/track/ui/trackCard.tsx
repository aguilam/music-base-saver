import Cover from "../../../shared/ui/cover";
import { formatTime } from "../../../shared/lib/utils";
import { A } from "@solidjs/router";
import { ShortTrack } from "../model/types";
import ArtistsNames from "~/entities/artists/ui/artistsNames";
import TrackPopover from "./trackPopover";
import { JSX, splitProps } from "solid-js";

interface TrackCardProps extends JSX.HTMLAttributes<HTMLDivElement> {
  content: ShortTrack;
  isAvatarHidden?: boolean;
}

const TrackCard = (props: TrackCardProps) => {
  const [local, rest] = splitProps(props, ["content", "isAvatarHidden"]);
  return (
    <TrackPopover track={local.content}>
      <A href={`/track/${local.content.id}`} class=" h-fit ring-0 not-hover:bg-transparent">
        <div class=" flex justify-between items-center" {...rest}>
          <div class="flex gap-3 items-center ">
            <div class="w-10 h-10 group relative flex items-center justify-center ">
              {!local.isAvatarHidden && (
                <Cover coverUri={local.content.coverUri} type="track" size="xs" />
              )}
            </div>
            <div>
              <p class={"text-primary-text"}>{local.content.title}</p>
              <ArtistsNames artists={local.content.artists} />
            </div>
          </div>
          <div class=" flex gap-5 items-center">
            <p class="text-secondary-text">{formatTime(local.content.duration ?? 0)}</p>
          </div>
        </div>
      </A>
    </TrackPopover>
  );
};

export default TrackCard;
