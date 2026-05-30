import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const tok = localStorage.getItem("auth.token");
  if (tok) config.headers.Authorization = `Bearer ${tok}`;
  return config;
});
