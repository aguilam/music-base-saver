import { Component, For } from "solid-js"
import { ServiceStatusCard } from "~/entities/core"
import { createStatusQuery } from "~/entities/core/api/queries"

const StatusesPage: Component = () => {
    const statusQuery = createStatusQuery()
    const status = () => statusQuery.data;
    return (
        <div>
            <div>
                <p>Downloader</p>
                <div class=" flex flex-col gap-2">
                    <For each={status()?.downloaders}>
                        {(item) => <ServiceStatusCard status={item} />}
                    </For>
                </div>
            </div>
            <div>
                <p>Importers</p>
                <div class=" flex flex-col gap-2">
                    <For each={status()?.importers}>
                        {(item) => <ServiceStatusCard status={item} />}
                    </For>
                </div>
            </div>
            <div>
                <p>Scrobblers</p>
                <div class=" flex flex-col gap-2">
                    <For each={status()?.scrobblers}>
                        {(item) => <ServiceStatusCard status={item} />}
                    </For>
                </div>
            </div>
            <div>
                <p>Search</p>
                <div class=" flex flex-col gap-2">
                    <For each={status()?.search}>
                        {(item) => <ServiceStatusCard status={item} />}
                    </For>
                </div>
            </div>
            <div>
                <p>Storages</p>
                <div class=" flex flex-col gap-2">
                    <For each={status()?.storages}>
                        {(item) => <ServiceStatusCard status={item} />}
                    </For>
                </div>
            </div>
        </div>
    )
}
export default StatusesPage