import { client } from "~/shared/api/client";
import { Sync } from "../model/types";

export async function getSyncs(){
    const syncs = await client.get(`/syncs`).json<Sync[]>()
    return syncs
}

export async function postSync(){
    const syncId = await client.post(`/syncs`).json<{"SyncId": string}>()
    return syncId
}

export async function getSync(id: string){
    const sync = await client.get(`/syncs/${id}`).json<Sync>()
    return sync
}

export async function cancelSync(id: string){
    const sync = await client.delete(`/syncs/${id}`)
    return sync
}