import React, { useEffect, useState } from "react";
import { Edit3, Sparkles, Trash2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import {
  BackButton,
  Button,
  ClothingForm,
  ClothingImage,
  ErrorAlert,
  Loading,
  Modal,
  OutfitCard,
} from "../components/UI";
import { formatCategorySlot } from "../constants";

export default function ClothingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [item, setItem] = useState(null);
  const [relatedOutfits, setRelatedOutfits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [modalError, setModalError] = useState("");

  useEffect(() => {
    Promise.all([api.getClothing(id), api.listOutfits()])
      .then(([itemData, outfitsData]) => {
        setItem(itemData);
        // Find outfits containing this item
        const matching = (outfitsData || []).filter((o) =>
          o.clothing_item_ids?.includes(id)
        );
        setRelatedOutfits(matching);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleDelete() {
    if (!window.confirm(`Delete "${item.name}" from your wardrobe?`)) return;
    try {
      await api.deleteClothing(id);
      navigate("/wardrobe");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpdate(formData) {
    setSavingEdit(true);
    setModalError("");

    try {
      const updated = await api.updateClothing(id, {
        name: formData.name,
        category: formData.category,
        color: formData.color,
        image: formData.imageFile,
      });

      setItem(updated);
      setEditModalOpen(false);
    } catch (err) {
      setModalError(err.message);
    } finally {
      setSavingEdit(false);
    }
  }

  if (loading) return <Loading message="Loading piece details…" />;
  if (error) return <ErrorAlert message={error} onRetry={() => navigate("/wardrobe")} />;
  if (!item) return null;

  return (
    <div>
      <BackButton to="/wardrobe" label="Back to wardrobe" />

      <div className="detail-layout">
        <div className="detail-image">
          <ClothingImage item={item} size="lg" />
        </div>

        <div className="detail-info">
          <div className="eyebrow">CLOTHING PIECE</div>
          <h1>{item.name}</h1>
          <p className="detail-lead">A piece from your personal collection.</p>

          <div className="detail-meta">
            <div>
              <span>Category</span>
              <strong>{formatCategorySlot(item.category)}</strong>
            </div>
            <div>
              <span>Color</span>
              <strong>{item.color}</strong>
            </div>
            <div>
              <span>Added</span>
              <strong>
                {item.created_at
                  ? new Date(item.created_at).toLocaleDateString()
                  : "Recently"}
              </strong>
            </div>
          </div>

          <div className="detail-actions">
            <Button
              icon={<Edit3 size={16} />}
              variant="secondary"
              onClick={() => setEditModalOpen(true)}
            >
              Edit piece
            </Button>
            <Button
              icon={<Trash2 size={16} />}
              variant="danger"
              onClick={handleDelete}
            >
              Delete
            </Button>
            <Button
              variant="secondary"
              icon={<Sparkles size={16} />}
              onClick={() => navigate("/stylist")}
            >
              Style with AI
            </Button>
          </div>
        </div>
      </div>

      {/* Styled Looks featuring this piece */}
      {relatedOutfits.length > 0 && (
        <section style={{ marginTop: "48px" }}>
          <div className="section-heading">
            <div>
              <div className="eyebrow">COMBINATIONS</div>
              <h2>Styled in {relatedOutfits.length} saved look{relatedOutfits.length > 1 ? "s" : ""}</h2>
            </div>
          </div>
          <div className="outfit-grid">
            {relatedOutfits.map((outfit) => (
              <OutfitCard
                key={outfit.id}
                outfit={outfit}
                clothesMap={{ [item.id]: item }}
                variant="compact"
              />
            ))}
          </div>
        </section>
      )}

      {/* Unified Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        eyebrow="EDIT CLOTHING"
        title="Update Piece"
      >
        <ClothingForm
          initialValues={item}
          onSubmit={handleUpdate}
          onCancel={() => setEditModalOpen(false)}
          submitLabel="Save changes"
          busy={savingEdit}
          error={modalError}
        />
      </Modal>
    </div>
  );
}
