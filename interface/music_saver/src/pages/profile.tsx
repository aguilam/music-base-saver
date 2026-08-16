import { useParams } from "@solidjs/router"
import { Component, createResource, createSignal, For, onMount } from "solid-js"
import { Playlist } from "~/entities/playlist"
import { createUserPlaylistsQuery } from "~/entities/playlist/api/queries"
import PlaylistCard from "~/entities/playlist/ui/playlistCard"
import { UserProfile } from "~/shared/api/types"
import { getUser } from "~/shared/api/users"

const ProfilePage: Component = () => {
    const params = useParams()
    const [user] = createResource(() => params.id!, getUser)
    const userPlaylistsQuery = createUserPlaylistsQuery(() => user()?.id!)
    const userPlaylists = () => userPlaylistsQuery.data
    return (
        <div class=" h-screen w-full">
            <div class="border-b-2 border-b-gray-300 w-full h-32 flex p-6 gap-4 items-center">
                <div class="w-16 h-16 bg-gray-600 flex items-center justify-center  rounded-full">
                    <p class="text-4xl text-gray-400 font-bold uppercase ">{user()?.username[0]}</p>
                </div>
                <p class="text-7xl font-extrabold text-gray-800">{user()?.username}</p>
            </div>
            <div class="w-full h-full px-4">
                <div>
                    <For each={userPlaylists()}>
                        {(playlist) => <PlaylistCard content={playlist} />}
                    </For>
                </div>
            </div>
        </div>
    )
}
export default ProfilePage
