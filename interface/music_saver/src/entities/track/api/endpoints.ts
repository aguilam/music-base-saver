import { client } from "~/shared/api/client";
import { ShortTrack } from "../model/types";
import { CursorResponse } from "~/shared/api/types";

export async function getTracks(cursor: string | null) {
    const tracks = await client.get("/tracks",{searchParams: cursor ? {cursor} : undefined }).json<CursorResponse<ShortTrack>>()
    return tracks
}