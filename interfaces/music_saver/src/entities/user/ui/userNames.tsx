import { For } from "solid-js"
import { ShortUser } from "../model/types"
import { A } from "@solidjs/router"

interface UserNamesProps {
    users: ShortUser[]
}

const UserNames = (props: UserNamesProps) => {
    return (
        <div class=" flex gap-1 text-black">
            <For each={props.users}>
                {(user) => <A href={`/profile/${user.id}`} class="text-black hover:text-gray-700">{user.username}</A>}
            </For>
        </div>
    )
}

export default UserNames