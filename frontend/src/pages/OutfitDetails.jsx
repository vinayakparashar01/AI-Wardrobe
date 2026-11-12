import React, { useEffect, useMemo, useState } from "react";
import { Check, Heart, Pencil, Plus, Shirt, Sparkles, Trash2, X } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import {
  BackButton,
  Button,
  ClothingImage,
  ErrorAlert,
  Loading,
  Modal,
  SearchInput,
} from "../components/UI";
import { formatCategorySlot } from "../constants";

export default function OutfitDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [outfit, setOutfit] = useState(null);
  const [allClothes, setAllClothes] = useState([]);
  const [clothesMap, setClothesMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editModalOpen, setEditModalOpen] = useState(false);

  // Edit modal state
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editIsFavorite, setEditIsFavorite] = useState(false);
  const [editSelectedIds, setEditSelectedIds] = useState([]);
  const [pieceSearch, setPieceSearch] = useState("");
  const [busySaving, setBusySaving] = useState(false);
  const [modalError, setModalError] = useState("");

  useEffect(() => {
    Promise.all([api.getOutfit(id), api.listClothes()])
      .then(([outfitData, clothesList]) => {
        setOutfit(outfitData);
        setAllClothes(clothesList || []);

        const map = {};
        (clothesList || []).forEach((c) => {
          map[c.id] = c;
        });
        setClothesMap(map);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const openEditModal = () => {
    if (!outfit) return;
    setEditName(outfit.name || "");
    setEditDescription(outfit.description || "");
    setEditIsFavorite(outfit.is_favorite || false);
    // Pre-populate with valid existing items currently in the user's wardrobe
    const currentValidIds = (outfit.clothing_item_ids || []).filter(
      (itemId) => Boolean(clothesMap[itemId])
    );
    setEditSelectedIds(currentValidIds);
    setPieceSearch("");
    setModalError("");
    setEditModalOpen(true);
  };

  const handleTogglePiece = (pieceId) => {
    setEditSelectedIds((prev) =>
      prev.includes(pieceId)
        ? prev.filter((item) => item !== pieceId)
        : [...prev, pieceId]
    );
  };

  const handleRemovePiece = (pieceId) => {
    setEditSelectedIds((prev) => prev.filter((item) => item !== pieceId));
  };

  const filteredCloset = useMemo(() => {
    if (!pieceSearch.trim()) return allClothes;
    const q = pieceSearch.toLowerCase();
    return allClothes.filter(
      (c) =>
        c.name?.toLowerCase().includes(q) ||
        c.category?.toLowerCase().includes(q) ||
        c.color?.toLowerCase().includes(q)
    );
  }, [allClothes, pieceSearch]);

  async function handleDelete() {
    if (!window.confirm(`Delete "${outfit.name}"?`)) return;
    try {
      await api.deleteOutfit(id);
      navigate("/outfits");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleToggleFavorite() {
    try {
      const updated = await api.updateOutfit(id, {
        is_favorite: !outfit.is_favorite,
      });
      setOutfit(updated);
      setEditIsFavorite(updated.is_favorite);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSaveEdit(e) {
    e.preventDefault();
    if (!editName.trim()) {
      setModalError("Please give your outfit a name.");
      return;
    }
    if (editSelectedIds.length < 1) {
      setModalError("Please select at least 1 clothing piece for this outfit.");
      return;
    }

    setBusySaving(true);
    setModalError("");

    try {
      const updated = await api.updateOutfit(outfit.id, {
        name: editName.trim(),
        description: editDescription.trim() || null,
        is_favorite: editIsFavorite,
        clothing_item_ids: editSelectedIds,
      });
      setOutfit(updated);
      setEditModalOpen(false);
    } catch (err) {
      setModalError(err.message);
    } finally {
      setBusySaving(false);
    }
  }

  if (loading) return <Loading message="Loading outfit details…" />;
  if (error) return <ErrorAlert message={error} onRetry={() => navigate("/outfits")} />;
  if (!outfit) return null;

  const pieces = (outfit.clothing_item_ids || [])
    .map((pieceId) => clothesMap[pieceId])
    .filter(Boolean);

  const isIncomplete =
    outfit.is_complete === false ||
    (outfit.clothing_item_ids && outfit.clothing_item_ids.length < 2) ||
    pieces.length < 2;

  return (
    <div>
      <BackButton to="/outfits" label="Back to outfits" />

      <div className="outfit-detail">
        <div className="outfit-detail-hero">
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap", marginBottom: "8px" }}>
            <span className="eyebrow" style={{ margin: 0 }}>SAVED LOOK</span>
            {isIncomplete && (
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "700",
                  background: "#fef3c7",
                  color: "#92400e",
                  padding: "3px 10px",
                  borderRadius: "12px",
                  border: "1px solid #fde68a",
                }}
              >
                ⚠️ Incomplete Outfit ({pieces.length} piece{pieces.length === 1 ? "" : "s"})
              </span>
            )}
          </div>

          <h1>{outfit.name}</h1>
          <p>{outfit.description || "A look made from your wardrobe pieces."}</p>

          <button
            className={`favorite-button ${outfit.is_favorite ? "liked" : ""}`}
            onClick={handleToggleFavorite}
          >
            <Heart
              size={18}
              fill={outfit.is_favorite ? "currentColor" : "none"}
            />
            <span>{outfit.is_favorite ? "Favorite Look" : "Add to Favorites"}</span>
          </button>
        </div>

        {/* Incomplete outfit warning banner */}
        {isIncomplete && (
          <div
            style={{
              background: "#fffbeb",
              border: "1px solid #fde68a",
              borderRadius: "14px",
              padding: "16px 20px",
              marginBottom: "24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "16px",
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "22px" }}>⚠️</span>
              <div>
                <strong style={{ color: "#92400e", fontSize: "14px" }}>
                  Some clothing items in this outfit are no longer available.
                </strong>
                <p style={{ margin: "3px 0 0", color: "#b45309", fontSize: "13px" }}>
                  This outfit has only {pieces.length} available piece{pieces.length === 1 ? "" : "s"}. At least 2 pieces are required for a complete look.
                </p>
              </div>
            </div>
            <Button
              variant="secondary"
              size="sm"
              icon={<Pencil size={14} />}
              onClick={openEditModal}
              style={{ borderColor: "#d97706", color: "#92400e", background: "#fff" }}
            >
              Add replacement pieces
            </Button>
          </div>
        )}

        {/* Pieces Grid */}
        <div className="detail-pieces">
          {pieces.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "36px",
                width: "100%",
                background: "#fbf6f5",
                borderRadius: "16px",
              }}
            >
              <Shirt size={36} color="#a3918d" style={{ marginBottom: "8px" }} />
              <p style={{ color: "var(--muted)", margin: "0 0 14px", fontSize: "14px" }}>
                All clothing items belonging to this outfit have been removed from your wardrobe.
              </p>
              <Button onClick={openEditModal} icon={<Plus size={15} />}>
                Add pieces to this outfit
              </Button>
            </div>
          ) : (
            pieces.map((piece, index) => (
              <div
                key={piece.id || index}
                className="detail-piece"
                onClick={() => navigate(`/wardrobe/${piece.id}`)}
                style={{ cursor: "pointer" }}
              >
                <ClothingImage item={piece} size="md" />
                <div>
                  <span>Piece 0{index + 1}</span>
                  <strong>{piece.name}</strong>
                  <p>
                    {formatCategorySlot(piece.category)}
                    {piece.color ? ` · ${piece.color}` : ""}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="detail-actions">
          <Button
            variant="secondary"
            icon={<Pencil size={16} />}
            onClick={openEditModal}
          >
            Edit outfit details
          </Button>
          <Button
            variant="danger"
            icon={<Trash2 size={16} />}
            onClick={handleDelete}
          >
            Delete outfit
          </Button>
          <Button
            variant="secondary"
            icon={<Sparkles size={16} />}
            onClick={() => navigate("/stylist")}
          >
            AI Stylist Studio
          </Button>
        </div>
      </div>

      {/* Unified Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        eyebrow="EDIT OUTFIT"
        title="Edit Outfit Details"
        maxWidth="680px"
      >
        <form className="form" onSubmit={handleSaveEdit}>
          {modalError && <ErrorAlert message={modalError} />}

          <label>
            Outfit Name
            <input
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="e.g. Classic Casual Look"
            />
          </label>

          <label>
            Description <span className="muted">(optional)</span>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Notes or styling instructions for this outfit..."
              rows="2"
            />
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={editIsFavorite}
              onChange={(e) => setEditIsFavorite(e.target.checked)}
            />
            <span>Mark as favorite look</span>
          </label>

          {/* Clothing Items Selector */}
          <div style={{ marginTop: "10px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <label style={{ margin: 0, fontWeight: "700", fontSize: "13px" }}>
                Outfit Pieces ({editSelectedIds.length} selected)
              </label>
              <span
                style={{
                  fontSize: "12px",
                  color: editSelectedIds.length >= 2 ? "#16a34a" : "#d97706",
                  fontWeight: "600",
                }}
              >
                {editSelectedIds.length >= 2
                  ? "✓ Complete look"
                  : `⚠️ Needs at least 2 pieces (currently ${editSelectedIds.length})`}
              </span>
            </div>

            {/* Selected chips row */}
            {editSelectedIds.length > 0 ? (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px",
                  padding: "10px",
                  background: "#f9efed",
                  borderRadius: "12px",
                  marginBottom: "14px",
                  maxHeight: "150px",
                  overflowY: "auto",
                }}
              >
                {editSelectedIds.map((pieceId) => {
                  const piece = clothesMap[pieceId];
                  return (
                    <div
                      key={pieceId}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        background: "#fff",
                        border: "1px solid #f3b9be",
                        borderRadius: "10px",
                        padding: "4px 8px",
                        fontSize: "12px",
                      }}
                    >
                      <ClothingImage item={piece} size="sm" />
                      <div style={{ lineHeight: "1.2" }}>
                        <strong style={{ fontSize: "12px" }}>{piece?.name || "Piece"}</strong>
                        <span style={{ display: "block", color: "var(--muted)", fontSize: "10px" }}>
                          {formatCategorySlot(piece?.category)} · {piece?.color}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemovePiece(pieceId)}
                        style={{
                          border: 0,
                          background: "#fee2e2",
                          color: "#b91c1c",
                          borderRadius: "50%",
                          width: "20px",
                          height: "20px",
                          display: "grid",
                          placeItems: "center",
                          cursor: "pointer",
                          marginLeft: "4px",
                        }}
                        title="Remove piece"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div
                style={{
                  padding: "16px",
                  background: "#f9efed",
                  borderRadius: "12px",
                  textAlign: "center",
                  color: "var(--muted)",
                  fontSize: "13px",
                  marginBottom: "14px",
                }}
              >
                No pieces selected. Add items from your closet below.
              </div>
            )}

            {/* Closet Search & Picker */}
            <div style={{ border: "1px solid var(--line)", borderRadius: "14px", padding: "14px", background: "#fff" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--muted)" }}>
                  YOUR WARDROBE
                </span>
                <span style={{ fontSize: "11px", color: "var(--muted)" }}>
                  Click items to toggle selection
                </span>
              </div>

              <SearchInput
                value={pieceSearch}
                onChange={setPieceSearch}
                placeholder="Search wardrobe pieces…"
                size="small"
              />

              <div
                style={{
                  marginTop: "10px",
                  maxHeight: "180px",
                  overflowY: "auto",
                  display: "grid",
                  gap: "6px",
                }}
              >
                {filteredCloset.length === 0 ? (
                  <div style={{ textAlign: "center", padding: "16px", color: "var(--muted)", fontSize: "12px" }}>
                    No matching clothing items found.
                  </div>
                ) : (
                  filteredCloset.map((item) => {
                    const isSelected = editSelectedIds.includes(item.id);
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handleTogglePiece(item.id)}
                        className={`picker-item ${isSelected ? "picked" : ""}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          cursor: "pointer",
                          padding: "6px 10px",
                          borderRadius: "10px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <div className="picker-image" style={{ width: "42px", height: "42px" }}>
                            <ClothingImage item={item} size="sm" />
                          </div>
                          <div style={{ textAlign: "left" }}>
                            <strong style={{ fontSize: "13px" }}>{item.name}</strong>
                            <span style={{ fontSize: "11px", color: "var(--muted)", display: "block" }}>
                              {formatCategorySlot(item.category)} · {item.color}
                            </span>
                          </div>
                        </div>

                        {isSelected ? (
                          <span
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              fontSize: "12px",
                              color: "#e11d48",
                              fontWeight: "600",
                              background: "#ffe4e6",
                              padding: "4px 8px",
                              borderRadius: "8px",
                            }}
                          >
                            <Check size={14} /> Selected
                          </span>
                        ) : (
                          <span
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              fontSize: "12px",
                              color: "var(--muted)",
                              padding: "4px 8px",
                              borderRadius: "8px",
                              border: "1px solid var(--line)",
                            }}
                          >
                            <Plus size={13} /> Add
                          </span>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          <div className="modal-actions" style={{ marginTop: "16px" }}>
            <Button
              variant="secondary"
              type="button"
              onClick={() => setEditModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={busySaving}>
              {busySaving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
