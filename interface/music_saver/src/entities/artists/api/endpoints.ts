import { client } from "~/shared/api/client";
import { Artist, ShortArtist } from "../model/types";
import { CursorResponse } from "~/shared/api/types";

export async function getArtists(cursor: string | null) {
    const artists = await client.get(`/artists`,{searchParams: cursor ? {cursor} : undefined }).json<CursorResponse<ShortArtist>>()
    return artists
}

export async function getArtist(id: number) {
    const artist = await client.get(`/artists/${id}`).json<Artist>()
    return artist
}