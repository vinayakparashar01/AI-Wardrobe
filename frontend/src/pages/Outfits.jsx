import React, { useEffect, useMemo, useState } from "react";
import { Plus, Sparkles } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import {
  Button,
  EmptyState,
  ErrorAlert,
  Loading,
  OutfitCard,
  PageHeader,
  SearchInput,
} from "../components/UI";

export default function Outfits() {
  const [items, setItems] = useState([]);
  const [clothes, setClothes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const searchQuery = searchParams.get("search") || "";
  const favoriteOnly = searchParams.get("favorite") === "1";

  async function loadData() {
    setLoading(true);
    try {
      const [outfitsData, clothesData] = await Promise.all([
        api.listOutfits(),
        api.listClothes(),
      ]);
      setItems(outfitsData || []);
      setClothes(clothesData || []);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const clothesMap = useMemo(() => {
    const map = {};
    clothes.forEach((c) => {
      map[c.id] = c;
    });
    return map;
  }, [clothes]);

  const handleSearchChange = (val) => {
    const newParams = new URLSearchParams(searchParams);
    if (!val) {
      newParams.delete("search");
    } else {
      newParams.set("search", val);
    }
    setSearchParams(newParams);
  };

  const handleFavoriteToggleFilter = () => {
    const newParams = new URLSearchParams(searchParams);
    if (favoriteOnly) {
      newParams.delete("favorite");
    } else {
      newParams.set("favorite", "1");
    }
    setSearchParams(newParams);
  };

  const filteredOutfits = useMemo(() => {
    return items.filter((outfit) => {
      const matchesFavorite = !favoriteOnly || outfit.is_favorite;
      const matchesSearch =
        !searchQuery ||
        `${outfit.name} ${outfit.description || ""}`
          .toLowerCase()
          .includes(searchQuery.toLowerCase());
      return matchesFavorite && matchesSearch;
    });
  }, [items, searchQuery, favoriteOnly]);

  const handleOutfitUpdate = (updated) => {
    setItems((prev) => prev.map((o) => (o.id === updated.id ? updated : o)));
  };

  return (
    <div>
      <PageHeader
        eyebrow="SAVED LOOKS"
        title={favoriteOnly ? "Favorite Outfits" : "Outfits"}
        subtitle={`${filteredOutfits.length} saved looks from your wardrobe.`}
        action={
          <div style={{ display: "flex", gap: "10px" }}>
            <Button
              variant="secondary"
              onClick={() => navigate("/stylist")}
              icon={<Sparkles size={16} />}
            >
              AI Stylist
            </Button>
            <Button
              onClick={() => navigate("/outfits/new")}
              icon={<Plus size={17} />}
            >
              Create outfit
            </Button>
          </div>
        }
      />

      <div className="toolbar">
        <SearchInput
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search outfits by name or description…"
          size="small"
        />
        <div className="category-tabs">
          <button
            className={!favoriteOnly ? "selected" : ""}
            onClick={() => handleFavoriteToggleFilter()}
          >
            All Outfits ({items.length})
          </button>
          <button
            className={favoriteOnly ? "selected" : ""}
            onClick={() => handleFavoriteToggleFilter()}
          >
            Favorites ({items.filter((o) => o.is_favorite).length})
          </button>
        </div>
      </div>

      <ErrorAlert
        message={error}
        onRetry={loadData}
        onDismiss={() => setError("")}
      />

      {loading ? (
        <Loading message="Loading your outfits…" />
      ) : filteredOutfits.length ? (
        <div className="outfit-grid">
          {filteredOutfits.map((outfit) => (
            <OutfitCard
              key={outfit.id}
              outfit={outfit}
              clothesMap={clothesMap}
              onUpdate={handleOutfitUpdate}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Plus />}
          title={favoriteOnly ? "No favorite looks yet" : "No saved looks yet"}
          text={
            favoriteOnly
              ? "Click the heart icon on any outfit to add it to your favorites."
              : "Let the AI Stylist curate outfit suggestions or combine pieces from your closet."
          }
          action={
            <div style={{ display: "flex", gap: "12px", marginTop: "14px" }}>
              <Button onClick={() => navigate("/stylist")}>
                Generate with AI Stylist
              </Button>
              <Button
                variant="secondary"
                onClick={() => navigate("/outfits/new")}
              >
                Create manually
              </Button>
            </div>
          }
        />
      )}
    </div>
  );
}
