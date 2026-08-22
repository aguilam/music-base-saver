import { useParams } from "@solidjs/router"
import { For } from "solid-js"
import { createSyncQuery } from "~/features/sync/api/queries"

const SyncPage = () => {
    const params = useParams()
    const sync = createSyncQuery(() => params.id!)
    const unboundFiles = () => {
        const unboundFiles: {"type": string,"path": string}[] = []
        sync.data?.result.unbound_files.covers.forEach((cover) => unboundFiles.push({type: "Cover",path: cover[0] + "/" + cover[1]}))
        sync.data?.result.unbound_files.lyrics.forEach((lyrics) => unboundFiles.push({type: "Lyrics",path: lyrics[0] + "/" + lyrics[1]}))
        sync.data?.result.unbound_files.videos.forEach((video) => unboundFiles.push({type: "Videos",path: video[0] + "/" + video[1]}))
        return unboundFiles
    }
    return (
        <div>
            <div class=" flex gap-2">
                <p>{sync.data?.progress}</p>
                <p>{sync.data?.status}</p>
                <p>{sync.data?.error}</p>
            </div>
            <div class="grid grid-cols-2 grid-rows-2 gap-3">
                <div>
                    <p>Tracks</p>
                    <p>Added: {sync.data?.result.tracks.added}/{sync.data?.result.tracks.searched_new}</p>
                    <div class=" flex gap-2">
                        <p>Deleted: {sync.data?.result.tracks.deleted}</p>
                        <p>Processed: {sync.data?.result.tracks.processed}</p>
                    </div>
                </div>
                <div>
                    <p>Lyrics</p>
                    <p>Added: {sync.data?.result.lyrics.added}/{sync.data?.result.lyrics.searched_new}</p>
                    <div class=" flex gap-2">
                        <p>Deleted: {sync.data?.result.lyrics.deleted}</p>
                        <p>Processed: {sync.data?.result.lyrics.processed}</p>
                    </div>
                </div>
                <div>
                    <p>Covers</p>
                    <p>Added: {sync.data?.result.covers.added}/{sync.data?.result.covers.searched_new}</p>
                    <div class=" flex gap-2">
                        <p>Deleted: {sync.data?.result.covers.deleted}</p>
                        <p>Processed: {sync.data?.result.covers.processed}</p>
                    </div>
                </div>
                <div>
                    <p>Videos</p>
                    <p>Added: {sync.data?.result.videos.added}/{sync.data?.result.videos.searched_new}</p>
                    <div class=" flex gap-2">
                        <p>Deleted: {sync.data?.result.videos.deleted}</p>
                        <p>Processed: {sync.data?.result.videos.processed}</p>
                    </div>
                </div>
            </div>
            <div class="flex flex-col gap-4">
                <For each={unboundFiles()}>
                    {(file) => <div class="flex gap-2 px-3 py-2 bg-gray-500"><p>{file.type}</p><p>{file.path}</p></div>}
                </For>
            </div>
        </div>
    )
}
export default SyncPage