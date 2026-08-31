import { Component, For } from "solid-js"
import { createUsersQuery } from "~/entities/user"
import { UserCard } from "~/entities/user/ui/userCard"

const UsersPage: Component = () => {
    const usersQuery = createUsersQuery()
    const users = () => usersQuery.data
    return (
        <div>
            <p>{users()?.length} Users</p>
            <For each={users()}>
                {(user) => <UserCard user={user} />}
            </For>
        </div>
    )
}
export default UsersPage