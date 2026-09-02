import { createQuery } from "@tanstack/solid-query";
import { getServerStatus } from "./endpoint";

export function createStatusQuery() {
    return createQuery(() => ({
        queryKey: ["serverStatus"],
        queryFn: () => getServerStatus()
    }))
}