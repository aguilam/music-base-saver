import { Component } from "solid-js"
import { Navigate } from "@solidjs/router"
const MainPage: Component = () => {
    return (
        <div>
            <Navigate href="/album/1"></Navigate>
            <p>Main</p>
        </div>
    )
}
export default MainPage
