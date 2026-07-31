import { client } from "~/shared/api/client";
import { Playlist } from "../model/types";

export async function getPlaylist(id: number) {
    const playlist = await client.get(`/playlists/${id}`).json<Playlist>()
    return playlist
}