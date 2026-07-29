import { client } from "./client";
import { UserProfile } from "./types";

export async function getUser(id: string) {
    return await client.get(`/users/${id}`).json<UserProfile>()
}