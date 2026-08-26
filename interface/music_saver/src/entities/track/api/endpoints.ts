import { client } from "~/shared/api/client";
import { FullTrack, ShortTrack } from "../model/types";
import { CursorResponse } from "~/shared/api/types";

export async function getTracks(cursor: string | null) {
    const tracks = await client.get("/tracks",{searchParams: cursor ? {cursor} : undefined }).json<CursorResponse<ShortTrack>>()
    return tracks
}

export async function getTrack(id: number) {
    const track = await client.get(`/tracks/${id}`).json<FullTrack>()
    return track
}