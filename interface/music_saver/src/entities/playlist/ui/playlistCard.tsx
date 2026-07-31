import { A } from "@solidjs/router";
import Cover from "../../../shared/ui/cover";
import { ShortPlaylist } from "../model/types";

interface PlaylistCardProps {
    content: ShortPlaylist;
}

const PlaylistCard = (props: PlaylistCardProps) => {
    return (
      	<A href={`/playlist/${props.content.id}`}>
        	<div class="w-56 p-0 ring-0 bg-transparent">
          		<div class="px-0">
            		<Cover coverUri={props.content.coverUri} type="playlist" size="lg" />
            		<p class="text-primary-text mt-2">{props.content.title}</p>
          		</div>
        	</div>
      	</A>
    );
  };
  
  export default PlaylistCard;