import { ListedUser } from "~/entities/user";
import { client } from "~/shared/api/client";

export async function refreshAuth() {
    try {
      await client.post("auth/refresh");
      return true;
    } catch {
      return false;
    }
  }
export async function loginAuth(username: string, password: string) {
    await client.post("/auth/login",{json:{username: username, password: password}})
}

export async function registerAuth(username: string, password: string) {
    await client.post("/auth/register",{json:{username: username, password: password}})
}

export async function logoutAuth() {
    await client.post("/auth/logout")
}

export async function getMe() {
    return await client.get("/auth/me").json<ListedUser>()
}

