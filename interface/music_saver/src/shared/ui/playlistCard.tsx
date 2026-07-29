import { A } from "@solidjs/router";
import { Playlist } from "../api/types";
import Cover from "./cover";

interface PlaylistCardProps {
    content: Playlist;
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