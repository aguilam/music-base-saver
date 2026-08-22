import { Sync } from "../model/types"
import { Button } from "~/components/ui/button"
import { Show } from "solid-js"
import { createCancelSyncMutation } from "../api/queries"

interface SyncCardProps{
    sync: Sync
}

const SyncCard = (props: SyncCardProps) => {
    const syncResult = () => props.sync.result
    const newContent = () => syncResult().covers.added + syncResult().lyrics.added + syncResult().videos.added + syncResult().tracks.added
    const deletedContent = () => syncResult().covers.deleted + syncResult().lyrics.deleted + syncResult().videos.deleted + syncResult().tracks.deleted
    const syncDeleteMutation = createCancelSyncMutation()
    const SyncDeleteHandler = () => {
        syncDeleteMutation.mutate(props.sync.id)
    }
    return (
        <div class=" py-2 px-4 bg-gray-500 flex justify-between">
            <div class=" flex gap-2">
                <p>New: {newContent()}</p>
                <p>Deleted: {deletedContent()}</p>
            </div>
            <div>
                <p>{props.sync.progress}</p>
                <p>{props.sync.status}</p>
                <Show when={props.sync.error}>
                    <p class="text-red-400">{props.sync.error}</p>
                </Show>
            </div>
            <Button variant={"destructive"} onClick={SyncDeleteHandler}>Cancel</Button>
        </div>
    )
}
export default SyncCard