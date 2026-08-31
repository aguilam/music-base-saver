import { A } from "@solidjs/router";
import Cover from "../../../shared/ui/cover";
import { ShortArtist } from "../model/types";

interface PlaylistCardProps {
    content: ShortArtist;
}

const ArtistCard = (props: PlaylistCardProps) => {
    return (
      	<A href={`/artist/${props.content.id}`}>
        	<div class="w-56 p-0 ring-0 bg-transparent">
          		<div class="flex flex-col items-center px-0">
            		<Cover coverUri={props.content.coverUri} type="artist" size="lg" />
            		<p class="text-primary-text mt-2">{props.content.name}</p>
          		</div>
        	</div>
      	</A>
    );
  };
  
  export default ArtistCard;