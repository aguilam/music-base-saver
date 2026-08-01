import { createQuery } from "@tanstack/solid-query";
import { Accessor } from "solid-js";
import { getPlaylist } from "./endpoints";

export function createPlaylistQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["playlist",id],
        queryFn: () => getPlaylist(id())
    }))
}