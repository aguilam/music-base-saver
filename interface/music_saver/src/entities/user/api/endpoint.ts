import { client } from "~/shared/api/client";
import { ListedUser } from "../model/types";

export async function getAllUsers() {
    const users = await client.get("/users").json<ListedUser[]>()
    return users
}