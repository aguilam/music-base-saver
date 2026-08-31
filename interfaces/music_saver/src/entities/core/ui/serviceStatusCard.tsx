import { ServiceStatus } from "../model/types"

interface StatusProps {
    status: ServiceStatus
}
export const ServiceStatusCard = (props: StatusProps) => {
    return (
        <div class=" flex gap-4 bg-gray-500 h-8 items-center mx-2 px-3">
            <p>{props.status.tag}</p>
            <div class="flex gap-1 items-center">
                <div class={`w-4 h-4 rounded-full ${props.status.health.ok ? "bg-green-600" : "bg-red-600"}`} />
                <p>{props.status.health.message}</p>
            </div>
        </div>
    )
}