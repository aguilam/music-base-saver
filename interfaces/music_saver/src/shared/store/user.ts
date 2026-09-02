import { createStore, SetStoreFunction } from "solid-js/store";
import { CurrentUser } from "../api/types";
import { makePersisted } from "@solid-primitives/storage";

const initialUser: CurrentUser = {
  id: NaN,
  username: "",
  role: "",
};

export const [user, setUser] = makePersisted<
  CurrentUser,
  [CurrentUser, SetStoreFunction<CurrentUser>]
>(createStore(initialUser), {
  name: "user",
});
