import { client } from "~/shared/api/client";
import { ShortTool } from "../model/types";

export async function getTrackTools() {
    const tools = await client.get("/tools/tracks").json<ShortTool[]>()
    return tools
}

export async function postTrackToolReq(trackId: number, toolId: string) {
    await client.post(`/tools/${toolId}/tracks/${trackId}`)
}