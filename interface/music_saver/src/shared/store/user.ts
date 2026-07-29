import { createStore } from "solid-js/store";
import { CurrentUser } from "../api/types";

export const [user,setUser] = createStore<CurrentUser>({
    id: "",
    username: "",
    role: ""
})