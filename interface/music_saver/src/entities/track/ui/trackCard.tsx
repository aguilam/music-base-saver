import Cover from "../../../shared/ui/cover";
import { formatTime } from "../../../shared/lib/utils";
import { A } from "@solidjs/router";
import { ShortTrack } from "../model/types";
import ArtistsNames from "~/entities/artists/ui/artistsNames";
interface TrackCardProps {
  content: ShortTrack;
  isAvatarHidden?: boolean;
}

const TrackCard = (props: TrackCardProps) => {
  return (
    <A
	href={`/track/${props.content.id}`}
      class=" h-fit ring-0 not-hover:bg-transparent"
    >
      <div class=" flex justify-between items-center">
        <div class="flex gap-3 items-center ">
          <div class="w-10 h-10 group relative flex items-center justify-center ">
            {!props.isAvatarHidden && <Cover coverUri={props.content.coverUri} type="track" size="xs" />}
          </div>
          <div>
            <p
              class={"text-primary-text"}
            >
              {props.content.title}
            </p>
            <ArtistsNames artists={props.content.artists}/>
          </div>
        </div>
        <div class=" flex gap-5 items-center">
          <p class="text-secondary-text">{formatTime(props.content.duration ?? 0)}</p>
        </div>
      </div>
    </A>
  );
};

export default TrackCard;