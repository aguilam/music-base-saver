import { client } from "~/shared/api/client";
import { Playlist, ShortPlaylist } from "../model/types";

export async function getPlaylist(id: number) {
    const playlist = await client.get(`/playlists/${id}`).json<Playlist>()
    return playlist
}

export async function getUserPlaylists(userId: number) {
    const playlists = await client.get(`/user/${userId}/playlists`).json<ShortPlaylist[]>()
    return playlists
}