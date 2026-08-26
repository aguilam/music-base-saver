import { createInfiniteQuery, createQuery } from "@tanstack/solid-query";
import { getTrack, getTracks } from "./endpoints";
import { Accessor } from "solid-js";


export function createTracksQuery() {
    return createInfiniteQuery(() => ({
        queryKey: ["tracks"],
        queryFn: ({pageParam}) => getTracks(pageParam),
        initialPageParam: null as string | null,
        getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.nextCursor : undefined,
    }))
}

export function createTrackQuery(id: Accessor<number>) {
    return createQuery(() => ({
        queryKey: ["track",id()],
        queryFn: () => getTrack(id())
    }))
}