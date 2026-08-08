import { createQuery } from "@tanstack/solid-query";
import { getAllUsers } from "./endpoint";

export function createUsersQuery() {
    return createQuery(() => ({
        queryKey: ["users"],
        queryFn: () => getAllUsers()
    }))
}