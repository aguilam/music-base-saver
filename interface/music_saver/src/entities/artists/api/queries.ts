import { createInfiniteQuery, createQuery } from "@tanstack/solid-query";
import { type Accessor } from "solid-js";
import { getArtist, getArtists } from "./endpoints";

export function createArtistsQuery() {
    return createInfiniteQuery(() => ({
        queryKey: ["artists"],
        queryFn: ({pageParam}) => getArtists(pageParam),
        initialPageParam: null as string | null,
        getNextPageParam: (lastPage) => lastPage.hasMore ? lastPage.nextCursor : undefined,
    }))
}

export function createArtistQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["artist",id()],
        queryFn: () => getArtist(id())
    }))
}