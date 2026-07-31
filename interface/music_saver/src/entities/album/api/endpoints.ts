import { client } from "~/shared/api/client";
import { Album } from "../model/types";

export async function getAlbum(id: number) {
    const album = await client.get(`/albums/${id}`).json<Album>()
    return album
}