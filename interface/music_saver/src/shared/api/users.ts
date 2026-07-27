import { client } from "./client";
import { UserProfile } from "./interfaces";

export async function getUser(id: string) {
    return await client.get(`/users/${id}`).json<UserProfile>()
}