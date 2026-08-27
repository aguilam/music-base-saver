import { useNavigate } from "@solidjs/router"
import { For } from "solid-js"
import { Button } from "~/components/ui/button"
import { createPlaylistMutation, createUserPlaylistsQuery } from "~/entities/playlist/api/queries"
import PlaylistCard from "~/entities/playlist/ui/playlistCard"
import { user } from "~/shared/store/user"

const PlaylistsPage = () => {
    const userPlaylistsQuery = createUserPlaylistsQuery(() => user.id)
    const userPlaylists = () => userPlaylistsQuery.data
    const navigate = useNavigate()
    const createPlaylist = createPlaylistMutation()
    const createPlaylistHandle = async () => {
        const playlist = await createPlaylist.mutateAsync({title: "My playlist",trackIds: [],ownerIds: [user.id],isPublic: false,})
        navigate(`/playlist/${playlist.id}`)
    }
    return (
        <div>
            <div class=" flex justify-between">
                <p>Playlists</p>
                <Button class=" text-2xl w-12 h-12 items-center" onclick={createPlaylistHandle}>+</Button>
            </div>
            <div class="grid grid-cols-[repeat(auto-fill,minmax(224px,1fr))] gap-4">
                <For each={userPlaylists()}>
                    {(item) => <PlaylistCard content={item}/>}
                </For>
            </div>
        </div>
    )
}

export default PlaylistsPage