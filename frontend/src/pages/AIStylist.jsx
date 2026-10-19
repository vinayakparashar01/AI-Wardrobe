import React, { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bookmark,
  Briefcase,
  Check,
  CloudRain,
  Compass,
  Footprints,
  GraduationCap,
  Heart,
  Infinity,
  Layers,
  PartyPopper,
  Pencil,
  Plus,
  RotateCw,
  Shirt,
  ShoppingBag,
  SlidersHorizontal,
  Snowflake,
  Sparkles,
  Sun,
  Watch,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api, getImageUrl } from "../api";
import { ClothingImage, ErrorAlert, Modal } from "../components/UI";
import { formatCategorySlot } from "../constants";

const OCCASIONS = [
  { id: "College / Everyday", label: "College / Everyday", icon: GraduationCap },
  { id: "Party", label: "Party", icon: PartyPopper },
  { id: "Formal / Interview", label: "Formal / Interview", icon: Briefcase },
  { id: "Date", label: "Date", icon: Heart },
  { id: "Custom", label: "Custom", icon: SlidersHorizontal },
];

const SEASONS = [
  { id: "Summer", label: "Summer", icon: Sun },
  { id: "Winter", label: "Winter", icon: Snowflake },
  { id: "Monsoon", label: "Monsoon", icon: CloudRain },
  { id: "Any", label: "Any", icon: Infinity },
];

const STYLES = [
  { id: "Casual", label: "Casual", icon: Shirt },
  { id: "Streetwear", label: "Streetwear", icon: Layers },
  { id: "Smart Casual", label: "Smart Casual", icon: ShoppingBag },
  { id: "Any", label: "Any", icon: Compass },
];

export default function AIStylist() {
  const navigate = useNavigate();

  // User Preferences
  const [occasion, setOccasion] = useState("College / Everyday");
  const [customOccasion, setCustomOccasion] = useState("");
  const [season, setSeason] = useState("Winter");
  const [style, setStyle] = useState("Casual");
  const [additionalRequirements, setAdditionalRequirements] = useState(
    "Comfortable for a full day."
  );

  // Data states
  const [clothes, setClothes] = useState([]);
  const [clothesLoaded, setClothesLoaded] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [toastMessage, setToastMessage] = useState("");

  // Change Item Modal State
  const [editingOutfitIndex, setEditingOutfitIndex] = useState(null);
  const [selectedSlotIndex, setSelectedSlotIndex] = useState(null);

  // Quick lookup map for clothes by id
  const clothesMap = useMemo(() => {
    const map = {};
    clothes.forEach((item) => {
      map[item.id] = item;
    });
    return map;
  }, [clothes]);

  // Load wardrobe on mount
  useEffect(() => {
    api
      .listClothes()
      .then((items) => {
        setClothes(items);
        setClothesLoaded(true);
      })
      .catch((err) => {
        setError(`Failed to load wardrobe: ${err.message}`);
        setClothesLoaded(true);
      });
  }, []);

  // Fetch recommendations
  async function generateOutfits(overridePrefs = null) {
    if (clothes.length < 2) {
      setError("Please add at least 2 clothing pieces to your wardrobe first.");
      return;
    }

    setLoading(true);
    setError("");

    const targetOccasion =
      (overridePrefs?.occasion || occasion) === "Custom"
        ? customOccasion.trim() || "Everyday"
        : overridePrefs?.occasion || occasion;
    const targetSeason = overridePrefs?.season || season;
    const targetStyle = overridePrefs?.style || style;
    const targetRequirements =
      overridePrefs?.additionalRequirements !== undefined
        ? overridePrefs.additionalRequirements
        : additionalRequirements;

    const payload = {
      occasion: targetOccasion,
      season: targetSeason,
      style: targetStyle,
      additional_requirements: targetRequirements.trim() || null,
    };

    try {
      const response = await api.recommendOutfits(payload);
      if (response && response.suggestions && response.suggestions.length) {
        const formatted = response.suggestions.map((s, idx) => ({
          ...s,
          tag: idx === 0 ? "Best Match" : "Trendy",
          saved: false,
          saving: false,
        }));
        setSuggestions(formatted);
      } else {
        throw new Error("No suggestions returned from AI stylist.");
      }
    } catch (err) {
      console.warn("AI generation note:", err.message);
      // Generate curated suggestions from user wardrobe if AI encounters temporary rate limit
      const fallback = buildCuratedFallback(
        clothes,
        targetOccasion,
        targetSeason,
        targetStyle,
        targetRequirements
      );
      if (fallback.length > 0) {
        setSuggestions(fallback);
      } else {
        setError(err.message || "Could not generate outfit suggestions.");
      }
    } finally {
      setLoading(false);
    }
  }

  // Auto-generate on initial wardrobe load if not yet generated
  useEffect(() => {
    if (clothesLoaded && clothes.length >= 2 && suggestions.length === 0 && !loading) {
      generateOutfits();
    }
  }, [clothesLoaded]);

  // Save outfit to database
  async function handleSaveOutfit(suggestionIndex) {
    const item = suggestions[suggestionIndex];
    if (!item || item.saved || item.saving) return;

    // Update UI saving state
    setSuggestions((prev) =>
      prev.map((s, idx) => (idx === suggestionIndex ? { ...s, saving: true } : s))
    );

    try {
      await api.createOutfit({
        name: item.name,
        description: item.explanation || `Curated for ${occasion} in ${season}`,
        clothing_item_ids: item.clothing_item_ids,
        is_favorite: suggestionIndex === 0,
      });

      setSuggestions((prev) =>
        prev.map((s, idx) =>
          idx === suggestionIndex ? { ...s, saved: true, saving: false } : s
        )
      );

      showToast(`"${item.name}" saved to your outfits!`);
    } catch (err) {
      setError(`Failed to save outfit: ${err.message}`);
      setSuggestions((prev) =>
        prev.map((s, idx) => (idx === suggestionIndex ? { ...s, saving: false } : s))
      );
    }
  }

  // Regenerate a single outfit card
  function handleRegenerateSingle(suggestionIndex) {
    if (!clothes.length) return;

    // Find pieces not fully used or permute category picks
    const current = suggestions[suggestionIndex];
    const currentIds = new Set(current?.clothing_item_ids || []);

    const uppers = clothes.filter(
      (c) => c.category?.toLowerCase() === "upper" && !currentIds.has(c.id)
    );
    const lowers = clothes.filter(
      (c) => c.category?.toLowerCase() === "lower" && !currentIds.has(c.id)
    );
    const shoes = clothes.filter(
      (c) => c.category?.toLowerCase() === "shoes" && !currentIds.has(c.id)
    );
    const accs = clothes.filter(
      (c) => c.category?.toLowerCase() === "accessories" && !currentIds.has(c.id)
    );

    const pick = (arr, fallbackArr) =>
      arr.length > 0
        ? arr[Math.floor(Math.random() * arr.length)]
        : fallbackArr[Math.floor(Math.random() * fallbackArr.length)];

    const allUppers = clothes.filter((c) => c.category?.toLowerCase() === "upper");
    const allLowers = clothes.filter((c) => c.category?.toLowerCase() === "lower");
    const allShoes = clothes.filter((c) => c.category?.toLowerCase() === "shoes");
    const allAccs = clothes.filter((c) => c.category?.toLowerCase() === "accessories");

    const newIds = [];
    const top = pick(uppers, allUppers);
    if (top) newIds.push(top.id);
    const bottom = pick(lowers, allLowers);
    if (bottom) newIds.push(bottom.id);
    const shoe = pick(shoes, allShoes);
    if (shoe) newIds.push(shoe.id);
    const acc = pick(accs, allAccs);
    if (acc) newIds.push(acc.id);

    if (newIds.length < 2) {
      // Pick any 2 distinct items
      newIds.length = 0;
      clothes.slice(0, 3).forEach((c) => newIds.push(c.id));
    }

    const titles = [
      "Effortless Campus Look",
      "Modern Street Casual",
      "Smart Layered Ensemble",
      "Refined Weekend Blend",
      "Relaxed Everyday Style",
    ];

    setSuggestions((prev) =>
      prev.map((s, idx) =>
        idx === suggestionIndex
          ? {
              ...s,
              name: titles[Math.floor(Math.random() * titles.length)],
              clothing_item_ids: newIds,
              explanation: `A freshly tuned combination balancing ${style.toLowerCase()} comfort and ${season.toLowerCase()} versatility.`,
              saved: false,
            }
          : s
      )
    );

    showToast("Refreshed outfit suggestion!");
  }

  // Replace a piece inside an outfit
  function handleReplacePiece(outfitIdx, oldItemId, newItemId) {
    setSuggestions((prev) =>
      prev.map((s, idx) => {
        if (idx !== outfitIdx) return s;
        const updatedIds = s.clothing_item_ids.map((id) =>
          id === oldItemId ? newItemId : id
        );
        return {
          ...s,
          clothing_item_ids: updatedIds,
          saved: false,
        };
      })
    );
    setEditingOutfitIndex(null);
    setSelectedSlotIndex(null);
    showToast("Outfit piece updated!");
  }

  function showToast(msg) {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage("");
    }, 3500);
  }

  return (
    <div className="stylist-container">
      {/* Top right "Personal AI Studio" tag */}
      <div className="stylist-top-banner">
        <span className="personal-ai-studio-badge">
          <Sparkles size={16} /> Personal AI Studio
        </span>
      </div>

      {/* Main Page Header */}
      <header className="stylist-header-row">
        <div className="stylist-header-left">
          <Sparkles size={32} className="sparkle-icon-coral" />
          <div>
            <h1>AI Stylist</h1>
            <p>Get personalized outfit suggestions using your own wardrobe.</p>
          </div>
        </div>

        <div className="stylist-header-right">
          <Sparkles size={28} className="sparkle-icon-coral" />
          <div>
            <h3>Style made personal</h3>
            <p>Your wardrobe + AI = Perfect looks</p>
          </div>
        </div>
      </header>

      {/* Toast notification */}
      {toastMessage && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "#1f1d1d",
            color: "#fff",
            padding: "12px 20px",
            borderRadius: "12px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.18)",
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontSize: "14px",
            fontWeight: "600",
          }}
        >
          <Check size={18} color="#4ade80" />
          {toastMessage}
        </div>
      )}

      {/* Error alert banner */}
      <ErrorAlert
        message={error}
        onRetry={() => {
          setError("");
          generateOutfits();
        }}
        onDismiss={() => setError("")}
      />

      {/* Preferences Card */}
      <section className="preferences-card">
        <h2 className="preferences-title">Tell us your preferences</h2>

        <div className="preferences-grid">
          {/* Column 1: Occasion */}
          <div className="pref-column">
            <span className="pref-label">Occasion</span>
            <div className="pref-pill-list">
              {OCCASIONS.map((occ) => {
                const IconComponent = occ.icon;
                const isSelected = occasion === occ.id;
                return (
                  <button
                    key={occ.id}
                    type="button"
                    className={`pref-pill-btn ${isSelected ? "active" : ""}`}
                    onClick={() => setOccasion(occ.id)}
                  >
                    <span className="pref-pill-icon">
                      <IconComponent size={15} />
                    </span>
                    <span>{occ.label}</span>
                  </button>
                );
              })}
            </div>

            {occasion === "Custom" && (
              <input
                className="custom-occasion-input"
                placeholder="Enter custom occasion..."
                value={customOccasion}
                onChange={(e) => setCustomOccasion(e.target.value)}
              />
            )}
          </div>

          {/* Column 2: Season */}
          <div className="pref-column">
            <span className="pref-label">Season</span>
            <div className="pref-pill-list">
              {SEASONS.map((seas) => {
                const IconComponent = seas.icon;
                const isSelected = season === seas.id;
                return (
                  <button
                    key={seas.id}
                    type="button"
                    className={`pref-pill-btn ${isSelected ? "active" : ""}`}
                    onClick={() => setSeason(seas.id)}
                  >
                    <span className="pref-pill-icon">
                      <IconComponent size={15} />
                    </span>
                    <span>{seas.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Column 3: Style */}
          <div className="pref-column">
            <span className="pref-label">Style</span>
            <div className="pref-pill-list">
              {STYLES.map((st) => {
                const IconComponent = st.icon;
                const isSelected = style === st.id;
                return (
                  <button
                    key={st.id}
                    type="button"
                    className={`pref-pill-btn ${isSelected ? "active" : ""}`}
                    onClick={() => setStyle(st.id)}
                  >
                    <span className="pref-pill-icon">
                      <IconComponent size={15} />
                    </span>
                    <span>{st.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Column 4: Additional requirements */}
          <div className="pref-column">
            <span className="pref-label">Additional requirements (optional)</span>
            <div className="textarea-container">
              <textarea
                className="requirements-textarea"
                maxLength={200}
                placeholder="Comfortable for a full day."
                value={additionalRequirements}
                onChange={(e) => setAdditionalRequirements(e.target.value)}
              />
              <span className="char-counter">
                {additionalRequirements.length}/200
              </span>
            </div>

            <button
              type="button"
              className="generate-btn"
              onClick={() => generateOutfits()}
              disabled={loading}
            >
              <Sparkles size={16} />
              <span>
                {loading ? "Generating suggestions…" : "Generate Outfit Suggestions"}
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* Wardrobe count warning if empty */}
      {clothesLoaded && clothes.length < 2 && (
        <div className="simple-empty" style={{ textAlign: "center", padding: "34px" }}>
          <h3>Your wardrobe needs at least 2 clothing pieces to style outfits.</h3>
          <p style={{ margin: "10px 0 16px" }}>
            Add items like shirts, pants, shoes, and accessories to unlock full AI styling.
          </p>
          <button
            className="button button-primary"
            onClick={() => navigate("/wardrobe?add=1")}
          >
            <Plus size={16} /> Add clothing piece
          </button>
        </div>
      )}

      {/* Suggestions Section */}
      <section className="suggestions-section">
        <div className="suggestions-header">
          <div className="suggestions-header-left">
            <Sparkles size={24} className="sparkle-icon-coral" />
            <div>
              <h2 className="suggestions-header-title">AI Outfit Suggestions</h2>
              <p className="suggestions-header-subtitle">
                Here are 3 outfits based on your preferences. You can edit any item or save
                your favorite!
              </p>
            </div>
          </div>

          <button
            type="button"
            className="regenerate-all-btn"
            onClick={() => generateOutfits()}
            disabled={loading}
          >
            <RotateCw size={15} className={loading ? "spin" : ""} />
            <span>Regenerate</span>
          </button>
        </div>

        {/* Loading Skeletons */}
        {loading && (
          <div className="suggestions-grid">
            {[1, 2, 3].map((num) => (
              <div key={num} className="suggestion-card" style={{ opacity: 0.85 }}>
                <div className="suggestion-card-top">
                  <div className="suggestion-title-group">
                    <span className="suggestion-number-badge">{num}</span>
                    <div
                      className="skeleton-box"
                      style={{ width: "140px", height: "18px" }}
                    />
                  </div>
                  <div
                    className="skeleton-box"
                    style={{ width: "70px", height: "20px", borderRadius: "12px" }}
                  />
                </div>

                <div className="outfit-pieces-row">
                  {[1, 2, 3, 4].map((p) => (
                    <div key={p} className="piece-thumbnail-card">
                      <div
                        className="skeleton-box"
                        style={{ width: "100%", height: "98px", borderRadius: "10px" }}
                      />
                      <div
                        className="skeleton-box"
                        style={{ width: "80%", height: "12px" }}
                      />
                      <div
                        className="skeleton-box"
                        style={{ width: "60%", height: "10px" }}
                      />
                    </div>
                  ))}
                </div>

                <div className="why-this-works-box">
                  <div
                    className="skeleton-box"
                    style={{ width: "110px", height: "14px", marginBottom: "8px" }}
                  />
                  <div
                    className="skeleton-box"
                    style={{ width: "100%", height: "42px" }}
                  />
                </div>

                <div className="card-actions-row">
                  <div
                    className="skeleton-box"
                    style={{ height: "36px", borderRadius: "10px" }}
                  />
                  <div
                    className="skeleton-box"
                    style={{ height: "36px", borderRadius: "10px" }}
                  />
                </div>
                <div
                  className="skeleton-box"
                  style={{ height: "42px", borderRadius: "10px" }}
                />
              </div>
            ))}
          </div>
        )}

        {/* Loaded Suggestions */}
        {!loading && suggestions.length > 0 && (
          <div className="suggestions-grid">
            {suggestions.map((outfit, index) => {
              const outfitPieces = outfit.clothing_item_ids
                .map((id) => clothesMap[id])
                .filter(Boolean);

              return (
                <article key={index} className="suggestion-card">
                  <div>
                    {/* Top title and badge */}
                    <div className="suggestion-card-top">
                      <div className="suggestion-title-group">
                        <span className="suggestion-number-badge">{index + 1}</span>
                        <h3 className="suggestion-name" title={outfit.name}>
                          {outfit.name}
                        </h3>
                      </div>
                      <span
                        className={`suggestion-tag ${
                          index === 0 ? "best-match" : "trendy"
                        }`}
                      >
                        {outfit.tag || (index === 0 ? "Best Match" : "Trendy")}
                      </span>
                    </div>

                    {/* Pieces row */}
                    <div className="outfit-pieces-row">
                      {outfitPieces.map((piece, pIdx) => (
                        <div key={piece.id || pIdx} className="piece-thumbnail-card">
                          <ClothingImage item={piece} size="sm" />
                          <strong className="piece-info-name" title={piece.name}>
                            {piece.name}
                          </strong>
                          <span className="piece-info-color" title={piece.color}>
                            {piece.color}
                          </span>
                          <span className="piece-info-slot">
                            ({formatCategorySlot(piece.category)})
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Why this works */}
                    <div className="why-this-works-box">
                      <div className="why-heading">
                        <Sparkles size={14} />
                        <span>Why this works</span>
                      </div>
                      <p className="why-text">{outfit.explanation}</p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div>
                    <div className="card-actions-row">
                      <button
                        type="button"
                        className="action-subtle-btn"
                        onClick={() => {
                          setEditingOutfitIndex(index);
                          setSelectedSlotIndex(0);
                        }}
                      >
                        <Pencil size={14} color="#ff5c70" />
                        <span>Change item</span>
                      </button>
                      <button
                        type="button"
                        className="action-subtle-btn"
                        onClick={() => handleRegenerateSingle(index)}
                      >
                        <RotateCw size={14} />
                        <span>Regenerate</span>
                      </button>
                    </div>

                    <button
                      type="button"
                      className={`save-outfit-btn ${outfit.saved ? "saved" : ""}`}
                      onClick={() => handleSaveOutfit(index)}
                      disabled={outfit.saved || outfit.saving}
                    >
                      {outfit.saved ? (
                        <>
                          <Check size={16} /> Saved Outfit
                        </>
                      ) : (
                        <>
                          <Bookmark size={16} />
                          {outfit.saving ? "Saving…" : "Save Outfit"}
                        </>
                      )}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Modal to Change Clothing Item */}
      {editingOutfitIndex !== null && suggestions[editingOutfitIndex] && (
        <ChangePieceModal
          outfit={suggestions[editingOutfitIndex]}
          clothes={clothes}
          clothesMap={clothesMap}
          onClose={() => {
            setEditingOutfitIndex(null);
            setSelectedSlotIndex(null);
          }}
          onReplace={(oldId, newId) =>
            handleReplacePiece(editingOutfitIndex, oldId, newId)
          }
        />
      )}
    </div>
  );
}

// Fallback icon when piece doesn't have a photo
function FallbackPieceIcon({ category, color }) {
  const cat = (category || "").toLowerCase();

  let Icon = Shirt;
  if (cat.includes("shoes") || cat.includes("footwear")) {
    Icon = Footprints;
  } else if (cat.includes("accessories") || cat.includes("watch")) {
    Icon = Watch;
  } else if (cat.includes("lower") || cat.includes("pant") || cat.includes("bottom")) {
    Icon = Layers;
  }

  return (
    <div className="piece-fallback-icon">
      <Icon size={26} />
    </div>
  );
}

function capitalizeSlot(category) {
  if (!category) return "Piece";
  const cat = category.toLowerCase();
  if (cat.includes("upper")) return "Upper";
  if (cat.includes("lower")) return "Lower";
  if (cat.includes("shoes")) return "Shoes";
  if (cat.includes("accessories")) return "Accessories";
  return category.charAt(0).toUpperCase() + category.slice(1);
}

// Helper to construct curated fallback combinations from wardrobe
function buildCuratedFallback(clothes, occasion, season, style, requirements) {
  if (clothes.length < 2) return [];

  const uppers = clothes.filter((c) => c.category?.toLowerCase() === "upper");
  const lowers = clothes.filter((c) => c.category?.toLowerCase() === "lower");
  const shoes = clothes.filter((c) => c.category?.toLowerCase() === "shoes");
  const accessories = clothes.filter((c) => c.category?.toLowerCase() === "accessories");

  const outfits = [
    {
      name: "Cozy Campus Casual",
      tag: "Best Match",
      slots: [
        uppers.find((c) => c.name.toLowerCase().includes("hoodie")) || uppers[0],
        lowers.find((c) => c.name.toLowerCase().includes("cargo") || c.name.toLowerCase().includes("pant")) || lowers[0],
        shoes.find((c) => c.color?.toLowerCase().includes("white")) || shoes[0],
        accessories.find((c) => c.name.toLowerCase().includes("backpack")) || accessories[0],
      ],
      explanation:
        "A comfortable and relaxed look perfect for college. The hoodie keeps you warm in winter, cargo pants are comfy for all-day wear, and sneakers give a casual, effortless vibe.",
    },
    {
      name: "Smart Casual Vibes",
      tag: "Trendy",
      slots: [
        uppers.find((c) => c.name.toLowerCase().includes("overshirt") || c.name.toLowerCase().includes("sweater") || c.name.toLowerCase().includes("shirt")) || uppers[1] || uppers[0],
        lowers.find((c) => c.name.toLowerCase().includes("jeans") && c.color?.toLowerCase().includes("blue")) || lowers[0],
        shoes.find((c) => c.color?.toLowerCase().includes("white") || c.name.toLowerCase().includes("sneaker")) || shoes[0],
        accessories.find((c) => c.name.toLowerCase().includes("watch")) || accessories[1] || accessories[0],
      ],
      explanation:
        "A simple yet stylish combination that looks great for college. The sweater keeps you warm, jeans are versatile and comfortable, and sneakers complete the casual smart look.",
    },
    {
      name: "Layered Street Style",
      tag: "Trendy",
      slots: [
        uppers.find((c) => c.name.toLowerCase().includes("shirt") || c.name.toLowerCase().includes("overshirt")) || uppers[0],
        uppers.find((c) => c.name.toLowerCase().includes("t-shirt") && c.color?.toLowerCase().includes("white")) || uppers[1] || uppers[0],
        lowers.find((c) => c.name.toLowerCase().includes("cargo") || c.name.toLowerCase().includes("jogger") || c.color?.toLowerCase().includes("black")) || lowers[1] || lowers[0],
        shoes.find((c) => c.color?.toLowerCase().includes("black") || c.name.toLowerCase().includes("sneaker")) || shoes[1] || shoes[0],
      ],
      explanation:
        "Layering adds warmth and style, while the neutral colors keep it versatile. This combo is comfortable, practical, and perfect for everyday wear in winter.",
    },
  ];

  return outfits.map((o) => {
    // Collect valid unique ids
    const validIds = [];
    const seen = new Set();
    o.slots.forEach((s) => {
      if (s && !seen.has(s.id)) {
        seen.add(s.id);
        validIds.push(s.id);
      }
    });

    // Ensure at least 2 items
    if (validIds.length < 2) {
      clothes.slice(0, 3).forEach((c) => {
        if (!seen.has(c.id)) {
          seen.add(c.id);
          validIds.push(c.id);
        }
      });
    }

    return {
      name: o.name,
      tag: o.tag,
      clothing_item_ids: validIds,
      explanation: o.explanation,
      saved: false,
      saving: false,
    };
  });
}

// Modal component for changing any piece in an outfit
function ChangePieceModal({ outfit, clothes, clothesMap, onClose, onReplace }) {
  const currentItems = outfit.clothing_item_ids.map((id) => clothesMap[id]).filter(Boolean);
  const [selectedPieceIndex, setSelectedPieceIndex] = useState(0);

  const activePiece = currentItems[selectedPieceIndex] || currentItems[0];
  const targetCategory = activePiece?.category?.toLowerCase() || "";

  // Available pieces in this category or all
  const availableAlternatives = useMemo(() => {
    return clothes.filter((c) => {
      // Must not already be in outfit
      if (outfit.clothing_item_ids.includes(c.id)) return false;
      // Filter by same category if possible
      if (targetCategory && c.category?.toLowerCase() === targetCategory) {
        return true;
      }
      return false;
    });
  }, [clothes, targetCategory, outfit]);

  // If no same-category alternatives, show all other clothes
  const displayAlternatives =
    availableAlternatives.length > 0
      ? availableAlternatives
      : clothes.filter((c) => !outfit.clothing_item_ids.includes(c.id));

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      eyebrow="CUSTOMIZE LOOK"
      title="Change Outfit Piece"
      maxWidth="560px"
    >
      <p style={{ fontSize: "13px", color: "var(--muted)", margin: "0 0 16px" }}>
        Select the piece in this outfit you want to swap out:
      </p>

      {/* Current pieces tabs */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${currentItems.length}, 1fr)`,
          gap: "8px",
          marginBottom: "20px",
        }}
      >
        {currentItems.map((item, idx) => {
          const isSelected = selectedPieceIndex === idx;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setSelectedPieceIndex(idx)}
              style={{
                border: isSelected ? "2px solid var(--accent)" : "1px solid var(--line)",
                background: isSelected ? "#ffe8eb" : "#ffffff",
                borderRadius: "10px",
                padding: "8px 6px",
                cursor: "pointer",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <ClothingImage item={item} size="sm" />
              <strong
                style={{
                  fontSize: "11px",
                  color: isSelected ? "var(--accent-dark)" : "var(--ink)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  width: "100%",
                }}
              >
                {item.name}
              </strong>
              <span style={{ fontSize: "10px", color: "var(--muted)" }}>
                {formatCategorySlot(item.category)}
              </span>
            </button>
          );
        })}
      </div>

      <h4 style={{ fontSize: "13px", margin: "0 0 10px 0" }}>
        Pick a replacement for "{activePiece?.name}":
      </h4>

      {displayAlternatives.length === 0 ? (
        <div className="simple-empty" style={{ padding: "20px", textAlign: "center" }}>
          No other clothes available to swap with. Add more pieces in your Wardrobe.
        </div>
      ) : (
        <div className="change-piece-grid">
          {displayAlternatives.map((alt) => (
            <div
              key={alt.id}
              className="piece-option-card"
              onClick={() => onReplace(activePiece.id, alt.id)}
            >
              <ClothingImage item={alt} size="sm" />
              <strong
                style={{
                  fontSize: "12px",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  maxWidth: "100%",
                }}
              >
                {alt.name}
              </strong>
              <span style={{ fontSize: "11px", color: "var(--muted)" }}>
                {alt.color} · {formatCategorySlot(alt.category)}
              </span>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 600,
                  color: "var(--accent)",
                  marginTop: "2px",
                }}
              >
                Select Piece
              </span>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}
