import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  Heart,
  Image as ImageIcon,
  MoreHorizontal,
  RotateCw,
  Search,
  UploadCloud,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api, getImageUrl } from "../api";
import { CATEGORIES, getCategoryInfo } from "../constants";

export function PageHeader({ eyebrow, title, subtitle, action }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function Button({ children, variant = "primary", icon, ...props }) {
  return (
    <button className={`button button-${variant}`} {...props}>
      {icon}
      {children}
    </button>
  );
}

export function BackButton({ to, label, onClick }) {
  const navigate = useNavigate();
  const handleClick = onClick || (() => (to ? navigate(to) : navigate(-1)));

  return (
    <button type="button" className="back-button" onClick={handleClick}>
      <ArrowLeft size={16} />
      <span>{label || "Back"}</span>
    </button>
  );
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search…",
  onClear,
  size = "normal",
  className = "",
}) {
  return (
    <div className={`search-input-wrapper search-${size} ${className}`}>
      <Search size={size === "small" ? 15 : 17} className="search-icon" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {value && (
        <button
          type="button"
          className="search-clear-btn"
          onClick={() => {
            if (onClear) onClear();
            else onChange("");
          }}
          aria-label="Clear search"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export function ErrorAlert({ message, onRetry, onDismiss }) {
  if (!message) return null;
  return (
    <div className="error-alert-banner">
      <div className="error-alert-content">
        <AlertCircle size={18} className="error-icon" />
        <span>{message}</span>
      </div>
      <div className="error-alert-actions">
        {onRetry && (
          <button type="button" onClick={onRetry} className="error-retry-btn">
            <RotateCw size={13} /> Try again
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="error-dismiss-btn"
            aria-label="Dismiss error"
          >
            <X size={15} />
          </button>
        )}
      </div>
    </div>
  );
}

export function Modal({
  isOpen,
  onClose,
  eyebrow,
  title,
  maxWidth = "520px",
  children,
}) {
  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(e) {
      if (e.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div
        className="modal"
        style={{ maxWidth }}
        onMouseDown={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="modal-head">
          <div>
            {eyebrow && <div className="eyebrow">{eyebrow}</div>}
            <h2>{title}</h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function ClothingImage({
  item,
  size = "md",
  className = "",
  showBadge = false,
}) {
  const [imageError, setImageError] = useState(false);
  const categoryInfo = getCategoryInfo(item?.category);
  const IconComponent = categoryInfo?.icon || ImageIcon;
  const imageUrl = getImageUrl(item?.image_url);

  // If item has a color, generate a subtle background tint
  const colorStr = (item?.color || "").toLowerCase();
  let tintBg = "#f7f2f1";
  if (colorStr.includes("white")) tintBg = "#fcfbfa";
  else if (colorStr.includes("black")) tintBg = "#242223";
  else if (colorStr.includes("blue") || colorStr.includes("navy")) tintBg = "#edf3fa";
  else if (colorStr.includes("beige") || colorStr.includes("khaki")) tintBg = "#f8f4ec";
  else if (colorStr.includes("grey") || colorStr.includes("gray")) tintBg = "#eeeeee";
  else if (colorStr.includes("brown")) tintBg = "#f6ede8";
  else if (colorStr.includes("green") || colorStr.includes("olive")) tintBg = "#eef4ed";

  const isDarkBg = colorStr.includes("black");

  return (
    <div
      className={`clothing-image-box size-${size} ${className}`}
      style={{
        backgroundColor: !imageUrl || imageError ? tintBg : undefined,
      }}
    >
      {imageUrl && !imageError ? (
        <img
          src={imageUrl}
          alt={item?.name || "Clothing piece"}
          onError={() => setImageError(true)}
          loading="lazy"
        />
      ) : (
        <div
          className="clothing-image-fallback"
          style={{ color: isDarkBg ? "#e8e5e6" : "#887b7a" }}
        >
          <IconComponent size={size === "lg" ? 56 : size === "sm" ? 22 : 36} />
          {size === "lg" && <span>{item?.name || "No photo available"}</span>}
        </div>
      )}
      {showBadge && categoryInfo && (
        <span className="clothing-slot-pill">{categoryInfo.shortLabel}</span>
      )}
    </div>
  );
}

export function ClothingCard({ item, onClick, onSelect, isSelected = false }) {
  const navigate = useNavigate();
  const handleClick = onClick || (() => navigate(`/wardrobe/${item.id}`));

  return (
    <article
      className={`clothing-card ${isSelected ? "selected" : ""}`}
      onClick={handleClick}
    >
      <div className="clothing-image">
        <ClothingImage item={item} size="full" />
      </div>
      <div className="card-info">
        <div>
          <h3>{item.name}</h3>
          <p>
            {item.category} · {item.color}
          </p>
        </div>
        {onSelect ? (
          <div className={`card-check ${isSelected ? "checked" : ""}`}>
            {isSelected && <Check size={14} />}
          </div>
        ) : (
          <MoreHorizontal size={18} className="card-more" />
        )}
      </div>
    </article>
  );
}

export function OutfitCard({
  outfit,
  clothesMap = {},
  onUpdate,
  variant = "default",
}) {
  const navigate = useNavigate();
  const [isFavorite, setIsFavorite] = useState(outfit.is_favorite);
  const [busy, setBusy] = useState(false);

  // Resolve pieces from clothesMap if available
  const pieces = (outfit.clothing_item_ids || [])
    .map((id) => (typeof id === "object" ? id : clothesMap[id]))
    .filter(Boolean);

  const toggleFavorite = async (e) => {
    e.stopPropagation();
    if (busy) return;
    setBusy(true);

    const nextState = !isFavorite;
    setIsFavorite(nextState);

    try {
      const updated = await api.updateOutfit(outfit.id, {
        is_favorite: nextState,
      });
      if (onUpdate) onUpdate(updated);
    } catch {
      setIsFavorite(!nextState); // revert
    } finally {
      setBusy(false);
    }
  };

  const handleCardClick = () => {
    navigate(`/outfits/${outfit.id}`);
  };

  // Compact card (used on Home page)
  if (variant === "compact") {
    return (
      <article className="outfit-card outfit-card-compact" onClick={handleCardClick}>
        <div className="outfit-collage-box">
          {pieces.length > 0 ? (
            <div
              className={`outfit-collage-grid count-${Math.min(pieces.length, 4)}`}
            >
              {pieces.slice(0, 4).map((p, idx) => (
                <div key={p.id || idx} className="collage-tile">
                  <ClothingImage item={p} size="sm" />
                </div>
              ))}
            </div>
          ) : (
            <div className="collage-empty">
              <span>{outfit.clothing_item_ids?.length || 0} pieces</span>
            </div>
          )}
        </div>
        <div className="card-info">
          <div>
            <h3>{outfit.name}</h3>
            <p>{outfit.description || "Saved combination"}</p>
          </div>
        </div>
      </article>
    );
  }

  // Full default card (used on Outfits page)
  return (
    <article className="outfit-card" onClick={handleCardClick}>
      <div className="outfit-visual-modern">
        <span className="outfit-count-pill">
          {outfit.clothing_item_ids?.length || pieces.length} pieces
        </span>

        {pieces.length > 0 ? (
          <div
            className={`outfit-collage-grid count-${Math.min(pieces.length, 4)}`}
          >
            {pieces.slice(0, 4).map((p, idx) => (
              <div key={p.id || idx} className="collage-tile">
                <ClothingImage item={p} size="sm" />
                <span className="tile-name">{p.name}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="collage-empty">
            <span>{outfit.clothing_item_ids?.length || 0} pieces</span>
          </div>
        )}

        <button
          className="card-heart-btn"
          onClick={toggleFavorite}
          aria-label={isFavorite ? "Remove favorite" : "Add to favorites"}
        >
          <Heart
            className={isFavorite ? "liked" : ""}
            size={18}
            fill={isFavorite ? "currentColor" : "none"}
          />
        </button>
      </div>

      <div className="card-info">
        <div>
          <h3>{outfit.name}</h3>
          <p>{outfit.description || "Saved look from your wardrobe"}</p>
        </div>
      </div>
    </article>
  );
}

export function ClothingForm({
  initialValues = {},
  onSubmit,
  onCancel,
  submitLabel = "Save Piece",
  busy = false,
  error = "",
}) {
  const [name, setName] = useState(initialValues.name || "");
  const [category, setCategory] = useState(initialValues.category || "Upper");
  const [color, setColor] = useState(initialValues.color || "");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(
    initialValues.image_url ? getImageUrl(initialValues.image_url) : null
  );

  const quickColors = [
    { name: "Black", hex: "#1f1d1d" },
    { name: "White", hex: "#ffffff", border: true },
    { name: "Navy Blue", hex: "#1e3a5f" },
    { name: "Beige", hex: "#d8c4b6" },
    { name: "Grey", hex: "#9e9e9e" },
    { name: "Brown", hex: "#7a5230" },
    { name: "Olive", hex: "#556b2f" },
  ];

  const handleFileChange = (e) => {
    const file = e.target.files?.[0] || null;
    setImageFile(file);

    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      name,
      category,
      color,
      imageFile,
    });
  };

  return (
    <form className="form clothing-form" onSubmit={handleSubmit}>
      {error && <ErrorAlert message={error} />}

      <label>
        Name
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Navy Blue Hoodie"
          autoFocus
        />
      </label>

      <div>
        <label style={{ display: "block", marginBottom: "8px" }}>Category</label>
        <div className="category-pill-selector">
          {CATEGORIES.map((cat) => {
            const IconComponent = cat.icon;
            const isSelected = category.toLowerCase() === cat.id.toLowerCase();
            return (
              <button
                key={cat.id}
                type="button"
                className={`category-selector-btn ${isSelected ? "selected" : ""}`}
                onClick={() => setCategory(cat.id)}
              >
                <IconComponent size={16} />
                <span>{cat.shortLabel}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label>
          Color
          <input
            required
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder="e.g. Navy Blue, White, Beige"
          />
        </label>
        <div className="quick-color-bubbles">
          {quickColors.map((c) => (
            <button
              key={c.name}
              type="button"
              className={`color-bubble ${color.toLowerCase() === c.name.toLowerCase() ? "active" : ""}`}
              onClick={() => setColor(c.name)}
              title={c.name}
              style={{
                backgroundColor: c.hex,
                border: c.border ? "1px solid #ddd" : "none",
              }}
            />
          ))}
        </div>
      </div>

      <div>
        <label>Photo</label>
        <div className="image-upload-zone">
          {imagePreview ? (
            <div className="upload-preview-container">
              <img src={imagePreview} alt="Preview" />
              <button
                type="button"
                className="remove-image-btn"
                onClick={() => {
                  setImageFile(null);
                  setImagePreview(null);
                }}
                title="Remove photo"
              >
                <X size={15} />
              </button>
            </div>
          ) : (
            <label className="upload-drop-area">
              <UploadCloud size={28} className="upload-icon" />
              <span>Click or drop image to upload</span>
              <span className="upload-hint">PNG, JPG, WEBP up to 5MB</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                style={{ display: "none" }}
              />
            </label>
          )}
        </div>
      </div>

      <div className="modal-actions">
        {onCancel && (
          <Button variant="secondary" type="button" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={busy}>
          {busy ? "Saving…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}

export function EmptyState({ icon, title, text, action }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h2>{title}</h2>
      <p>{text}</p>
      {action}
    </div>
  );
}

export function Loading({ message = "Loading…" }) {
  return (
    <div className="loading-state">
      <span className="spinner" />
      <span>{message}</span>
    </div>
  );
}
