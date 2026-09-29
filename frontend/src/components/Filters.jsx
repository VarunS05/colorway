export default function Filters({ colors, tags, selectedColor, selectedTag, onColorChange, onTagChange }) {
  return (
    <div className="filters">
      <div className="filter-group" role="group" aria-label="Filter by color">
        <button
          className={selectedColor === "" ? "active" : ""}
          onClick={() => onColorChange("")}
        >
          All colors
        </button>
        {colors.map((hex) => (
          <button
            key={hex}
            className={selectedColor === hex ? "active swatch-button" : "swatch-button"}
            style={{ backgroundColor: hex }}
            aria-label={`Filter by ${hex}`}
            aria-pressed={selectedColor === hex}
            onClick={() => onColorChange(hex)}
          />
        ))}
      </div>

      <select
        aria-label="Filter by tag"
        value={selectedTag}
        onChange={(e) => onTagChange(e.target.value)}
      >
        <option value="">All tags</option>
        {tags.map((tag) => (
          <option key={tag} value={tag}>
            {tag}
          </option>
        ))}
      </select>
    </div>
  );
}
