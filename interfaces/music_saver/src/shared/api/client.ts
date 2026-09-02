import ky from "ky";
import { refreshAuth } from "./auth";

const API_URL = "http://127.0.0.1:8000";

const api = ky.create({
    baseUrl: API_URL,
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
    },
    parseJson: (text) => {
		return JSON.parse(text, (_, value) => {
			if (value && value.coverId != null) {
			  value.coverUri = `${API_URL}/covers/${value.coverId}`;
			}
      if (value && value.duration != null) {
        value.duration /= 1000
      }
			return value;
		  });
	}
})