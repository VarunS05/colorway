export default function Gallery({ items, onDelete }) {
  if (items.length === 0) {
    return <p className="empty-state">No images yet — upload one to get started.</p>;
  }

  return (
    <div className="gallery-grid">
      {items.map((item) => (
        <figure key={item.id} className="gallery-item">
          <img src={item.url} alt={item.sourceKey || item.id} loading="lazy" />
          <figcaption>
            {item.colorway?.hex && (
              <span
                className="swatch"
                data-testid="swatch"
                style={{ backgroundColor: item.colorway.hex }}
                title={item.colorway.hex}
              />
            )}
            <div className="tags">
              {(item.tags || []).map((tag) => (
                <span className="tag" key={tag.name}>
                  {tag.name}
                </span>
              ))}
            </div>
            {onDelete && (
              <button onClick={() => onDelete(item.id)} aria-label={`Delete ${item.id}`}>
                Delete
              </button>
            )}
          </figcaption>
        </figure>
      ))}
    </div>
  );
}
