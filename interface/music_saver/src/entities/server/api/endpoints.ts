import { client } from "~/shared/api/client";
import { ServerStats } from "../model/types";

export async function getConfig() {
    const config = await client.get('/config').text()
    return config
}

export async function changeConfig(config: string) {
    await client.put(`/config`,{body: config, headers: {'Content-Type': 'text/plain'}})
}

export async function getServerStats() {
    return await client.get("/stats").json<ServerStats>()
}