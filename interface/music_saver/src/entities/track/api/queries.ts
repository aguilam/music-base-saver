import { createInfiniteQuery } from "@tanstack/solid-query";
import { getTracks } from "./endpoints";


export function createTracksQuery() {
    return createInfiniteQuery(() => ({
        queryKey: ["tracks"],
        queryFn: ({pageParam}) => getTracks(pageParam),
        initialPageParam: null as string | null,
        getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.nextCursor : undefined,
    }))
}