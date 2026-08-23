import { client } from "~/shared/api/client";
import { Album, ShortAlbum } from "../model/types";
import { CursorResponse } from "~/shared/api/types";

export async function getAlbums(cursor: string | null) {
    const albums = await client.get("/albums",{searchParams: cursor ? {cursor} : undefined }).json<CursorResponse<ShortAlbum>>()
    return albums
}

export async function getAlbum(id: number) {
    const album = await client.get(`/albums/${id}`).json<Album>()
    return album
}