
import { cn } from "~/lib/utils";
import { tailwindSizeClasses } from "./helpers";
import CoverPlaceholder from "../cover-placeholder";
import { createEffect, createSignal, Show } from "solid-js";

interface CoverProps {
	coverUri: string | null;
	type: "artist" | "album" | "track" | "playlist";
	size: "xs" | "sm" | "md" | "lg";
}

const Cover = (props: CoverProps) => {
	const isRoundedCard = () => props.type === "artist";
	const [status, setStatus] = createSignal(props.coverUri ? "loading" : "error");
	createEffect(() => {
		setStatus(props.coverUri ? "loading" : "error");
	});
	
	return (
    	<>
			<Show when={status() !== "loaded"}>
				<CoverPlaceholder icon={props.type} size={props.size} rounded={isRoundedCard()} />
			</Show>

			<Show when={props.coverUri && status() !== "error"}>
				<img
    	    	  src={props.coverUri!}
    	    	  alt={`${props.type} cover`}
    	    	  loading="lazy"
    	    	  decoding="async"
    	    	  onLoad={() => setStatus("loaded")}
    	    	  onError={() => setStatus("error")}
    	    	  class={cn(
    	    	    "object-cover rounded-lg ",
    	    	    tailwindSizeClasses[props.size],
    	    	    isRoundedCard() && "rounded-full",
    	    	    status() !== "loaded" && "invisible absolute",
    	    	  )}
    	    	/>
			</Show>
    	</>
	);
};

export default Cover;