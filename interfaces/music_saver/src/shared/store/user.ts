import { createStore, SetStoreFunction } from "solid-js/store";
import { makePersisted } from "@solid-primitives/storage";
import { ListedUser } from "~/entities/user";

const initialUser: ListedUser = {
  id: NaN,
  username: "",
  isAdmin: false,
};

export const [user, setUser] = makePersisted<
ListedUser,
  [ListedUser, SetStoreFunction<ListedUser>]
>(createStore(initialUser), {
  name: "user",
});
