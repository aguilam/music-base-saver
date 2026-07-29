import { useParams } from "@solidjs/router"
import { Component, createSignal, onMount } from "solid-js"
import { UserProfile } from "~/shared/api/types"
import { getUser } from "~/shared/api/users"

const ProfilePage: Component = () => {
    const [user, setUser] = createSignal<UserProfile>()
    const params = useParams()
    onMount(async () => {
        const userProfile = await getUser(params.id!)
        setUser(userProfile)
    })
    return (
        <div class=" h-screen w-full">
            <div class="border-b-2 border-b-gray-300 w-full h-32 flex p-6 gap-4 items-center">
                <div class="w-16 h-16 bg-gray-600 flex items-center justify-center  rounded-full">
                    <p class="text-4xl text-gray-400 font-bold uppercase ">{user()?.username[0]}</p>
                </div>
                <p class="text-7xl font-extrabold text-gray-800">{user()?.username}</p>
            </div>
            <div class="w-full h-full px-4">
                <p>Content</p>
            </div>
        </div>
    )
}
export default ProfilePage
