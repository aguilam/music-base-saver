import { client } from "~/shared/api/client";

export async function getConfig() {
    const config = await client.get('/config').text()
    return config
}

export async function changeConfig(config: string) {
    await client.put(`/config`,{body: config, headers: {'Content-Type': 'text/plain'}})
}