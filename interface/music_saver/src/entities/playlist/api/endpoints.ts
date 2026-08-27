import { client } from "~/shared/api/client";
import { Playlist, ShortPlaylist } from "../model/types";

export async function getPlaylist(id: number) {
    const playlist = await client.get(`/playlists/${id}`).json<Playlist>()
    return playlist
}

export async function deletePlaylist(id: number) {
    const playlist = await client.delete(`/playlists/${id}`)
}

export async function patchPlaylist(id: number, title: string | null = null, trackIds: number[] | null = null, ownerIds: number[] | null = null, isPublic: boolean | null = null) {
    const playlist = await client.patch(`/playlists/${id}`,{json: {title: title, track_ids: trackIds, owner_ids: ownerIds, is_public: isPublic}}).json<Playlist>()
    return playlist
}

export async function createPlaylist(title: string, trackIds: number[], ownerIds: number[], isPublic: boolean) {
    const playlist = await client.post("/playlists",{json: {title: title, track_ids: trackIds, owner_ids: ownerIds, is_public: isPublic}}).json<Playlist>()
    return playlist
}

export async function getUserPlaylists(userId: number) {
    const playlists = await client.get(`/user/${userId}/playlists`).json<ShortPlaylist[]>()
    return playlists
}