import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { createUser, getAllUsers, getUser, pathUser } from "./endpoint";
import { Accessor } from "solid-js";

export function createUsersQuery() {
  return createQuery(() => ({
    queryKey: ["users"],
    queryFn: () => getAllUsers(),
  }));
}

export function createUserQuery(id: Accessor<number>) {
  return createQuery(() => ({
    queryKey: ["users",id()],
    queryFn: () => getUser(id()),
  }));
}

export function pathUsersMutation() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (data: { userId: number; username: string; password: string }) =>
      pathUser(data.userId, data.username, data.password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  }));
}

export function addUserMutation() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (data: { username: string; password: string }) =>
      createUser(data.username, data.password),
    onSuccess: () => {
      queryClient.refetchQueries({ queryKey: ["users"] });
    },
  }));
}
