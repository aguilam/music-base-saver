import { client } from "~/shared/api/client";
import { ListedUser } from "../model/types";

export async function getAllUsers() {
  const users = await client.get("/users").json<ListedUser[]>();
  return users;
}

export async function pathUser(userId: number, username: string, password: string) {
  await client.patch(`/users/${userId}`, { json: { username: username, password: password } });
}
