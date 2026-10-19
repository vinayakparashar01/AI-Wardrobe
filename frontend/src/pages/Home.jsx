import React, { useEffect, useMemo, useState } from "react";
import { ArrowRight, Layers3, Plus, Shirt, Sparkles, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { api } from "../api";
import { Button, ClothingCard, Loading, OutfitCard } from "../components/UI";

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [clothes, setClothes] = useState([]);
  const [outfits, setOutfits] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listClothes(), api.listOutfits()])
      .then(([clothesData, outfitsData]) => {
        setClothes(clothesData || []);
        setOutfits(outfitsData || []);
      })
      .catch((err) => console.error("Error loading home data:", err))
      .finally(() => setLoading(false));
  }, []);

  const clothesMap = useMemo(() => {
    const map = {};
    clothes.forEach((item) => {
      map[item.id] = item;
    });
    return map;
  }, [clothes]);

  if (loading) return <Loading message="Loading your wardrobe studio…" />;

  const favoriteOutfitsCount = outfits.filter((x) => x.is_favorite).length;

  return (
    <div>
      {/* Hero Banner */}
      <section className="hero-banner">
        <div>
          <div className="eyebrow">PERSONAL AI STUDIO</div>
          <h1>
            Good day, <em>{user?.name || "there"}</em>
          </h1>
          <p>
            Your wardrobe currently has {clothes.length} curated pieces. Ask the AI Stylist
            to design outfits or explore your closet combinations.
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <Button
            onClick={() => navigate("/stylist")}
            icon={<Sparkles size={17} />}
          >
            AI Stylist
          </Button>
          <Button
            variant="secondary"
            onClick={() => navigate("/wardrobe?add=1")}
            icon={<Plus size={17} />}
          >
            Add Piece
          </Button>
        </div>
      </section>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card" onClick={() => navigate("/wardrobe")} style={{ cursor: "pointer" }}>
          <Shirt />
          <div>
            <strong>{clothes.length}</strong>
            <span>Pieces in wardrobe</span>
          </div>
        </div>

        <div className="stat-card" onClick={() => navigate("/outfits")} style={{ cursor: "pointer" }}>
          <Layers3 />
          <div>
            <strong>{outfits.length}</strong>
            <span>Saved outfits</span>
          </div>
        </div>

        <div className="stat-card" onClick={() => navigate("/outfits?favorite=1")} style={{ cursor: "pointer" }}>
          <Star />
          <div>
            <strong>{favoriteOutfitsCount}</strong>
            <span>Favorite looks</span>
          </div>
        </div>
      </div>

      {/* Recently Added Clothes */}
      <section className="home-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">YOUR CLOSET</div>
            <h2>Recently added</h2>
          </div>
          <button
            className="text-button"
            onClick={() => navigate("/wardrobe")}
          >
            View wardrobe <ArrowRight size={16} />
          </button>
        </div>

        {clothes.length ? (
          <div className="clothing-grid home-grid">
            {clothes.slice(0, 4).map((item) => (
              <ClothingCard key={item.id} item={item} />
            ))}
          </div>
        ) : (
          <div className="simple-empty">
            Your wardrobe is ready for its first piece.{" "}
            <button onClick={() => navigate("/wardrobe?add=1")}>
              Add clothing piece
            </button>
          </div>
        )}
      </section>

      {/* Saved Looks */}
      <section className="home-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">SAVED LOOKS</div>
            <h2>Your outfits</h2>
          </div>
          <button className="text-button" onClick={() => navigate("/outfits")}>
            View all <ArrowRight size={16} />
          </button>
        </div>

        {outfits.length ? (
          <div className="outfit-grid">
            {outfits.slice(0, 3).map((outfit) => (
              <OutfitCard
                key={outfit.id}
                outfit={outfit}
                clothesMap={clothesMap}
                variant="compact"
              />
            ))}
          </div>
        ) : (
          <div className="simple-empty">
            No outfits yet. Let the{" "}
            <button onClick={() => navigate("/stylist")}>
              AI Stylist generate looks
            </button>{" "}
            from your wardrobe pieces.
          </div>
        )}
      </section>
    </div>
  );
}
