import { createEffect, For, ParentProps } from "solid-js"
import { ShortTrack } from "../model/types"
import { createTrackToolsQuery, postTrackToolReqMutation } from "~/entities/tool"
import { ContextMenu, ContextMenuContent, ContextMenuItem, ContextMenuPortal, ContextMenuTrigger } from "~/shared/ui/context-menu/contextMenu"

interface TrackPopoverProps extends ParentProps {
    track: ShortTrack
}

const TrackPopover = (props:TrackPopoverProps) => {
    const PopoverFunctions = [
        {"title": "Change", "function": () => console.log("change")},
        {"title": "Delete", "function": () => console.log("delete")}
    ]
    
    const trackToolsQuery = createTrackToolsQuery()
    const trackToolMutation = postTrackToolReqMutation()

    createEffect(() => {
        if (!trackToolsQuery.data) return

        for(const tool of trackToolsQuery.data) {
            PopoverFunctions.push({"title": tool.toolName,"function": () => trackToolMutation.mutate({toolId: tool.toolId, trackId: props.track.id})})
        }
    })

    return (
        <ContextMenu>
            <ContextMenuTrigger>
                {props.children}
            </ContextMenuTrigger>
            <ContextMenuPortal>
                <ContextMenuContent class=' w-20'>
                    <For each={PopoverFunctions}>
                      {(func) => (
                        <ContextMenuItem onClick={func.function}>{func.title}</ContextMenuItem>
                      )}
                    </For>
                </ContextMenuContent>
            </ContextMenuPortal>
        </ContextMenu>
    )
}

export default TrackPopover