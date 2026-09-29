const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function listImages({ color, tag } = {}) {
  const params = new URLSearchParams();
  if (color) params.set("color", color);
  if (tag) params.set("tag", tag);
  const query = params.toString() ? `?${params.toString()}` : "";

  const res = await fetch(`${API_BASE}/images/all${query}`);
  if (!res.ok) throw new Error(`Failed to list images: ${res.status}`);
  return res.json();
}

export async function deleteImage(id) {
  const res = await fetch(`${API_BASE}/images/delete/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete image: ${res.status}`);
  return res.json();
}

async function getUploadUrl(filename, contentType) {
  const params = new URLSearchParams({ filename, contentType });
  const res = await fetch(`${API_BASE}/images/upload-url?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to get upload URL: ${res.status}`);
  return res.json();
}

// Uploads directly to S3 via a presigned URL (not proxied through the API) --
// the backend only ever hands back a signed URL, never touches image bytes.
export async function uploadImage(file) {
  const { uploadUrl, key } = await getUploadUrl(file.name, file.type || "image/png");
  const putRes = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type || "image/png" },
    body: file,
  });
  if (!putRes.ok) throw new Error(`Upload to S3 failed: ${putRes.status}`);
  return { key };
}
