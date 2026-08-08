import { A } from "@solidjs/router"
import { ListedUser } from "../model/types"
import { Show } from "solid-js"
interface userCardProps {
    user: ListedUser
}
export const UserCard = (props: userCardProps) => {
    return (
        <A href={`/profile/${props.user.id}`} class=" flex justify-between bg-gray-600 mx-2 p-3">
            <p>{props.user.username}</p>
            <Show when={props.user.isAdmin}>
                <div class="bg-green-700 border-green-800 text-white rounded-lg p-3 flex items-center h-4">
                    <p>Admin</p>
                </div>
            </Show>
        </A>
    )
} 