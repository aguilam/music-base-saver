import { createMutation } from "@tanstack/solid-query"
import { loginAuth, logoutAuth, registerAuth } from "./endpoints";

  
export function createRegisterMutation() {
  return createMutation(() => ({
    mutationFn: (data: { username: string; password: string }) =>
      registerAuth(data.username, data.password)
  }));
}

export function createLoginMutation() {
  return createMutation(() => ({
    mutationFn: (data: { username: string; password: string }) =>
      loginAuth(data.username, data.password)
  }));
}

export function createLogoutMutation() {
  return createMutation(() => ({
    mutationFn: () => logoutAuth()
  }));
}