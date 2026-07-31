import { client } from "~/shared/api/client";
import { Artist } from "../model/types";

export async function getArtist(id: number) {
    const artist = await client.get(`/artists/${id}`).json<Artist>()
    return artist
}