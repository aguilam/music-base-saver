import { createStore } from "solid-js/store";
import { CurrentUser } from "../api/types";
import { makePersisted } from "@solid-primitives/storage";

const initialUser: CurrentUser = {
    id: "",
    username: "",
    role: ""
  };

export const [user,setUser] = makePersisted(createStore(initialUser)as any,
    {name: "user"}
);
