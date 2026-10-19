import React, { useEffect, useMemo, useState } from "react";
import { Check, Shirt, Sparkles, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import {
  BackButton,
  Button,
  ClothingImage,
  ErrorAlert,
  Loading,
  SearchInput,
} from "../components/UI";
import { formatCategorySlot } from "../constants";

export default function CreateOutfit() {
  const navigate = useNavigate();

  const [clothes, setClothes] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listClothes()
      .then((items) => setClothes(items || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filteredClothes = useMemo(() => {
    return clothes.filter((item) =>
      `${item.name} ${item.category} ${item.color}`
        .toLowerCase()
        .includes(searchQuery.toLowerCase())
    );
  }, [clothes, searchQuery]);

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const removePiece = (id) => {
    setSelectedIds((prev) => prev.filter((item) => item !== id));
  };

  async function handleSave() {
    if (!name.trim()) {
      setError("Please give your outfit a name.");
      return;
    }
    if (selectedIds.length < 2) {
      setError("Please select at least 2 clothing pieces for a complete outfit.");
      return;
    }

    setBusy(true);
    setError("");

    try {
      const outfit = await api.createOutfit({
        name,
        description: description || null,
        clothing_item_ids: selectedIds,
        is_favorite: isFavorite,
      });
      navigate(`/outfits/${outfit.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loading message="Loading your closet…" />;

  return (
    <div>
      <BackButton to="/outfits" label="Back to outfits" />

      <div className="create-layout">
        {/* Left Column: Builder Preview & Info */}
        <section className="outfit-builder">
          <div className="eyebrow">CREATE A LOOK</div>
          <h1>Build your outfit</h1>
          <p className="builder-subtitle">
            Choose pieces from your wardrobe and see your combination come together.
          </p>

          <div className="builder-preview">
            {selectedIds.length ? (
              selectedIds.map((id, index) => {
                const item = clothes.find((c) => c.id === id);
                return (
                  <div
                    className={`preview-piece preview-${index % 3}`}
                    key={id}
                  >
                    <button
                      type="button"
                      className="preview-remove-chip"
                      onClick={() => removePiece(id)}
                      title="Remove piece"
                    >
                      <X size={13} />
                    </button>
                    <ClothingImage item={item} size="md" />
                    <span className="preview-label">{item?.name}</span>
                  </div>
                );
              })
            ) : (
              <div className="preview-empty">
                <Shirt size={36} />
                <span>Select pieces from your closet on the right</span>
              </div>
            )}
          </div>

          <div className="form">
            <label>
              Outfit Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Cozy Campus Layer"
              />
            </label>

            <label>
              Description <span className="muted">(optional)</span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What makes this combination great?"
                rows="3"
              />
            </label>

            <label className="check-row">
              <input
                type="checkbox"
                checked={isFavorite}
                onChange={(e) => setIsFavorite(e.target.checked)}
              />
              <span>Save as favorite look</span>
            </label>

            <ErrorAlert message={error} onDismiss={() => setError("")} />

            <div style={{ display: "flex", gap: "12px", marginTop: "10px" }}>
              <Button onClick={handleSave} disabled={busy}>
                {busy ? "Saving outfit…" : "Save outfit"}
              </Button>
              <Button
                variant="secondary"
                type="button"
                onClick={() => navigate("/stylist")}
                icon={<Sparkles size={16} />}
              >
                Or use AI Stylist
              </Button>
            </div>
          </div>
        </section>

        {/* Right Column: Closet Picker */}
        <aside className="closet-picker">
          <div className="picker-head">
            <div>
              <div className="eyebrow">YOUR CLOSET</div>
              <h2>Select pieces</h2>
            </div>
            <span className="selection-count">
              {selectedIds.length} selected
            </span>
          </div>

          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search closet…"
            size="small"
          />

          <div className="picker-list">
            {filteredClothes.map((item) => {
              const isSelected = selectedIds.includes(item.id);
              return (
                <button
                  key={item.id}
                  type="button"
                  className={`picker-item ${isSelected ? "picked" : ""}`}
                  onClick={() => toggleSelect(item.id)}
                >
                  <div className="picker-image">
                    <ClothingImage item={item} size="sm" />
                  </div>
                  <div>
                    <strong>{item.name}</strong>
                    <span>
                      {formatCategorySlot(item.category)} · {item.color}
                    </span>
                  </div>
                  {isSelected && <Check size={18} className="picker-check-icon" />}
                </button>
              );
            })}
          </div>
        </aside>
      </div>
    </div>
  );
}
