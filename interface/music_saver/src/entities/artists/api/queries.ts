import { createQuery } from "@tanstack/solid-query";
import { type Accessor } from "solid-js";
import { getArtist } from "./endpoints";

export function createArtistQuery(id: Accessor<number>){
    return createQuery(() => ({
        queryKey: ["artist",id()],
        queryFn: () => getArtist(id())
    }))
}