import { A } from "@solidjs/router"
import { ListedUser } from "../model/types"
import { Show } from "solid-js"
import { Badge } from "~/shared/ui/badge/badge"
interface userCardProps {
    user: ListedUser
}
export const UserCard = (props: userCardProps) => {
    return (
        <A href={`/profile/${props.user.id}`} class=" flex justify-between bg-gray-600 mx-2 p-3">
            <p>{props.user.username}</p>
            <Show when={props.user.isAdmin}>
                <Badge variant="secondary">Admin</Badge>
            </Show>
        </A>
    )
} 