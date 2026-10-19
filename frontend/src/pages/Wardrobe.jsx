import React, { useEffect, useMemo, useState } from "react";
import { Plus, Search, Sparkles } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { CATEGORIES } from "../constants";
import {
  Button,
  ClothingCard,
  ClothingForm,
  EmptyState,
  ErrorAlert,
  Loading,
  Modal,
  PageHeader,
  SearchInput,
} from "../components/UI";

export default function Wardrobe() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [savingPiece, setSavingPiece] = useState(false);
  const [modalError, setModalError] = useState("");

  const categoryParam = searchParams.get("category") || "All";
  const searchParam = searchParams.get("search") || "";
  const sortParam = searchParams.get("sort") || "";
  const isAddModalOpen = searchParams.get("add") === "1";

  async function loadWardrobe() {
    setLoading(true);
    try {
      const clothes = await api.listClothes();
      setItems(clothes || []);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWardrobe();
  }, []);

  const handleCategoryChange = (cat) => {
    const newParams = new URLSearchParams(searchParams);
    if (cat === "All") {
      newParams.delete("category");
    } else {
      newParams.set("category", cat);
    }
    setSearchParams(newParams);
  };

  const handleSearchChange = (val) => {
    const newParams = new URLSearchParams(searchParams);
    if (!val) {
      newParams.delete("search");
    } else {
      newParams.set("search", val);
    }
    setSearchParams(newParams);
  };

  const closeAddModal = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("add");
    setSearchParams(newParams);
    setModalError("");
  };

  const openAddModal = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("add", "1");
    setSearchParams(newParams);
  };

  async function handleCreatePiece(formData) {
    setSavingPiece(true);
    setModalError("");

    try {
      const createdItem = await api.createClothing({
        name: formData.name,
        category: formData.category,
        color: formData.color,
        image: formData.imageFile,
      });

      setItems((prev) => [createdItem, ...prev]);
      closeAddModal();
    } catch (err) {
      setModalError(err.message);
    } finally {
      setSavingPiece(false);
    }
  }

  const categoryCounts = useMemo(() => {
    const counts = { All: items.length };
    CATEGORIES.forEach((cat) => {
      counts[cat.id] = items.filter(
        (i) => i.category?.toLowerCase() === cat.id.toLowerCase()
      ).length;
    });
    return counts;
  }, [items]);

  const filteredItems = useMemo(() => {
    let result = items.filter((item) => {
      const matchesCategory =
        categoryParam === "All" ||
        item.category?.toLowerCase() === categoryParam.toLowerCase();
      const matchesSearch =
        !searchParam ||
        `${item.name} ${item.category} ${item.color}`
          .toLowerCase()
          .includes(searchParam.toLowerCase());
      return matchesCategory && matchesSearch;
    });

    if (sortParam === "recent") {
      result = [...result].sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
    }

    return result;
  }, [items, categoryParam, searchParam, sortParam]);

  return (
    <div>
      <PageHeader
        eyebrow="MY COLLECTION"
        title="My wardrobe"
        subtitle={`${items.length} pieces, ready to style.`}
        action={
          <div style={{ display: "flex", gap: "10px" }}>
            <Button
              variant="secondary"
              onClick={() => navigate("/stylist")}
              icon={<Sparkles size={16} />}
            >
              AI Stylist
            </Button>
            <Button onClick={openAddModal} icon={<Plus size={17} />}>
              Add piece
            </Button>
          </div>
        }
      />

      <div className="toolbar">
        <SearchInput
          value={searchParam}
          onChange={handleSearchChange}
          placeholder="Search pieces by name, color…"
          size="small"
        />

        <div className="category-tabs">
          <button
            className={categoryParam === "All" ? "selected" : ""}
            onClick={() => handleCategoryChange("All")}
          >
            All ({categoryCounts.All || 0})
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className={
                categoryParam.toLowerCase() === cat.id.toLowerCase()
                  ? "selected"
                  : ""
              }
              onClick={() => handleCategoryChange(cat.id)}
            >
              {cat.shortLabel} ({categoryCounts[cat.id] || 0})
            </button>
          ))}
        </div>
      </div>

      <ErrorAlert
        message={error}
        onRetry={loadWardrobe}
        onDismiss={() => setError("")}
      />

      {loading ? (
        <Loading message="Loading wardrobe pieces…" />
      ) : filteredItems.length ? (
        <div className="clothing-grid">
          {filteredItems.map((item) => (
            <ClothingCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Search />}
          title={searchParam ? "No pieces found" : "Your closet is waiting"}
          text={
            searchParam
              ? `No items match "${searchParam}". Try a different search or clear filters.`
              : "Start by adding your first clothing piece or exploring styling ideas."
          }
          action={
            <Button onClick={openAddModal} icon={<Plus size={16} />}>
              Add your first piece
            </Button>
          }
        />
      )}

      {/* Unified Add Modal using shared Modal and ClothingForm */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={closeAddModal}
        eyebrow="WARDROBE"
        title="Add Clothing Piece"
      >
        <ClothingForm
          onSubmit={handleCreatePiece}
          onCancel={closeAddModal}
          submitLabel="Add to wardrobe"
          busy={savingPiece}
          error={modalError}
        />
      </Modal>
    </div>
  );
}
