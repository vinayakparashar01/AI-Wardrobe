import React, { useEffect, useState } from "react";
import { Heart, Pencil, Sparkles, Trash2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import {
  BackButton,
  Button,
  ClothingImage,
  ErrorAlert,
  Loading,
  Modal,
} from "../components/UI";
import { formatCategorySlot } from "../constants";

export default function OutfitDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [outfit, setOutfit] = useState(null);
  const [clothesMap, setClothesMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editModalOpen, setEditModalOpen] = useState(false);

  // Edit modal state
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editIsFavorite, setEditIsFavorite] = useState(false);
  const [busySaving, setBusySaving] = useState(false);
  const [modalError, setModalError] = useState("");

  useEffect(() => {
    Promise.all([api.getOutfit(id), api.listClothes()])
      .then(([outfitData, clothesList]) => {
        setOutfit(outfitData);
        setEditName(outfitData.name || "");
        setEditDescription(outfitData.description || "");
        setEditIsFavorite(outfitData.is_favorite || false);

        const map = {};
        (clothesList || []).forEach((c) => {
          map[c.id] = c;
        });
        setClothesMap(map);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

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
    setBusySaving(true);
    setModalError("");

    try {
      const updated = await api.updateOutfit(outfit.id, {
        name: editName,
        description: editDescription || null,
        is_favorite: editIsFavorite,
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

  return (
    <div>
      <BackButton to="/outfits" label="Back to outfits" />

      <div className="outfit-detail">
        <div className="outfit-detail-hero">
          <div className="eyebrow">SAVED LOOK</div>
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

        {/* Pieces Grid */}
        <div className="detail-pieces">
          {pieces.map((piece, index) => (
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
          ))}
        </div>

        <div className="detail-actions">
          <Button
            variant="secondary"
            icon={<Pencil size={16} />}
            onClick={() => setEditModalOpen(true)}
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
        title="Update Details"
      >
        <form className="form" onSubmit={handleSaveEdit}>
          {modalError && <ErrorAlert message={modalError} />}

          <label>
            Outfit Name
            <input
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
          </label>

          <label>
            Description <span className="muted">(optional)</span>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows="3"
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

          <div className="modal-actions">
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
