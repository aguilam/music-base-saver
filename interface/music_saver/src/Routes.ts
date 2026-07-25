import { lazy } from "solid-js";
import App from "./App";

export const routes = [
    {
        path: "/auth",
        component: lazy(() => import("./pages/auth")),
    },
    {
        path: "/",
        component: App,
        children: [
            {
                path: "/",
                component: lazy(() => import("./pages/main")),
            },
            {
                path: "/statuses",
                component: lazy(() => import("./pages/statuses")),
            },
            {
                path: "/search",
                component: lazy(() => import("./pages/search")),
            },
            {
                path: "/settings",
                component: lazy(() => import("./pages/settings")),
            },
            {
                path: "/users",
                component: lazy(() => import("./pages/users")),
            },
            {
                path: "/profile/:id",
                component: lazy(() => import("./pages/profile")),
            },
            {
                path: "/artist/:id",
                component: lazy(() => import("./pages/artist")),
            },
            {
                path: "/album/:id",
                component: lazy(() => import("./pages/album")),
            },
            {
                path: "/playlist/:id",
                component: lazy(() => import("./pages/playlist")),
            },
            {
                path: "/track/:id",
                component: lazy(() => import("./pages/track")),
            },
        ]
    }
]