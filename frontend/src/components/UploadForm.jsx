import { useState } from "react";

export default function UploadForm({ onUpload }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  async function handleChange(e) {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await onUpload(file);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <div className="upload-form">
      <label htmlFor="upload-input">
        {uploading ? "Uploading…" : "Upload image"}
      </label>
      <input id="upload-input" type="file" accept="image/*" onChange={handleChange} disabled={uploading} />
      {error && <p className="error" role="alert">{error}</p>}
    </div>
  );
}
