import { createQuery } from "@tanstack/solid-query";
import { Accessor } from "solid-js";
import { getPlaylist, getUserPlaylists } from "./endpoints";

export function createPlaylistQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["playlist",id()],
        queryFn: () => getPlaylist(id())
    }))
}

export function createUserPlaylistsQuery(userId: Accessor<number>) {
    return createQuery(() => ({
        queryKey: ["user-playlist",userId()],
        queryFn: () => getUserPlaylists(userId())
    }))
}