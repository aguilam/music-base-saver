import { cn } from "~/lib/utils";
import { sizeClasses, iconClasses, iconSizes } from "./helpers";

interface CoverPlaceholderProps {
	rounded?: boolean;
	icon: "artist" | "album" | "track" | "playlist";
	size: "xs" | "sm" | "md" | "lg";
}

const CoverPlaceholder = (props: CoverPlaceholderProps) => {
	const Icon = iconClasses[props.icon];
	return (
		<div
			class={cn(
        	"w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center",
        	props?.rounded === true && "rounded-full",
        	sizeClasses[props.size],
			)}
		>
    		<p class="text-white" style={{ "font-size": props.size }} >{Icon}</p>
    	</div>
  );
};
export default CoverPlaceholder;