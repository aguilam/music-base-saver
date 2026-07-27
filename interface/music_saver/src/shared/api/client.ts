import ky from "ky";
import { refreshAuth } from "./auth";

const api = ky.create({
    baseUrl: "http://127.0.0.1:8000",
    credentials: "include",
  });

export const client = api.extend({
    hooks:{
        afterResponse: [
            async ({request,options, response}) => {
                const url = new URL(request.url);

                if (
                  response.status !== 401 ||
                  url.pathname === "/auth/refresh" ||
                  url.pathname === "/auth/login" ||
                  url.pathname === "/auth/register"
                ) {
                  return response;
                }
        
                const refreshed = await refreshAuth();
                if (!refreshed) return response;
        
                return api(request, options);
            }
        ]
    }
})