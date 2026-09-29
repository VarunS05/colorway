import { useEffect, useMemo, useState } from "react";
import { listImages, uploadImage, deleteImage } from "./api";
import Gallery from "./components/Gallery";
import Filters from "./components/Filters";
import UploadForm from "./components/UploadForm";

export default function App() {
  const [items, setItems] = useState([]);
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedTag, setSelectedTag] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function refresh(filters = {}) {
    setLoading(true);
    setError(null);
    try {
      const data = await listImages(filters);
      setItems(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh({ color: selectedColor, tag: selectedTag });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedColor, selectedTag]);

  const colors = useMemo(
    () => [...new Set(items.map((item) => item.colorway?.hex).filter(Boolean))],
    [items]
  );
  const tags = useMemo(
    () => [...new Set(items.flatMap((item) => (item.tags || []).map((t) => t.name)))],
    [items]
  );

  async function handleUpload(file) {
    await uploadImage(file);
    // The pipeline (thumbnail -> color -> tags -> DynamoDB) runs async in
    // AWS after this returns, so the new item won't appear until it
    // completes -- a real product would poll or use a websocket here.
    setTimeout(() => refresh({ color: selectedColor, tag: selectedTag }), 5000);
  }

  async function handleDelete(id) {
    await deleteImage(id);
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  return (
    <div className="app">
      <h1>Colorway</h1>
      <UploadForm onUpload={handleUpload} />
      <Filters
        colors={colors}
        tags={tags}
        selectedColor={selectedColor}
        selectedTag={selectedTag}
        onColorChange={setSelectedColor}
        onTagChange={setSelectedTag}
      />
      {loading && <p>Loading…</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {!loading && !error && <Gallery items={items} onDelete={handleDelete} />}
    </div>
  );
}
