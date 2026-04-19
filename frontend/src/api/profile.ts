// src/api/profile.ts
import api from "../services/api";

export async function uploadFoto(file: File) {
  const formData = new FormData();
  formData.append("foto", file);

  const { data } = await api.post("/me/foto/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })

  return data;
}