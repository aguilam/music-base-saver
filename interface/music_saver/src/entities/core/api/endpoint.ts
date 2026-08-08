import { client } from "~/shared/api/client";
import { StatusResponse } from "../model/types";

export async function getServerStatus() {
    const statuses = await client.get("/status").json<StatusResponse>()
    return statuses
}