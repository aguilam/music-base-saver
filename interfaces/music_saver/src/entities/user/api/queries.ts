import { createMutation, createQuery, useQueryClient } from "@tanstack/solid-query";
import { createUser, getAllUsers, pathUser } from "./endpoint";

export function createUsersQuery() {
  return createQuery(() => ({
    queryKey: ["users"],
    queryFn: () => getAllUsers(),
  }));
}

export function pathUsersMutation() {
  const queryClient = useQueryClient();
  return createMutation(() => ({
    mutationFn: (data: { userId: number; username: string; password: string }) =>
      pathUser(data.userId, data.username, data.password),
    onSuccess: (_, data) => {
      queryClient.invalidateQueries({ queryKey: ["user", data.userId] });
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
