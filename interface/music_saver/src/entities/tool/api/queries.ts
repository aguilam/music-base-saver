import { createMutation, createQuery } from "@tanstack/solid-query";
import { getTrackTools, postTrackToolReq } from "./endpoints";

export function createTrackToolsQuery() {
    return createQuery(() => ({
        queryKey: ["track-tools"],
        queryFn: () => getTrackTools()
    }))
}

export function postTrackToolReqMutation() {
    return createMutation(() => ({
        mutationFn: (data: {trackId: number, toolId: string}) => postTrackToolReq(data.trackId,data.toolId)
    }))
}