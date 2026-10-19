import { Footprints, Layers, Shirt, Watch } from "lucide-react";

export const CATEGORIES = [
  {
    id: "Upper",
    label: "Tops (Upper)",
    shortLabel: "Upper",
    description: "Shirts, T-shirts, Hoodies, Jackets",
    icon: Shirt,
  },
  {
    id: "Lower",
    label: "Bottoms (Lower)",
    shortLabel: "Lower",
    description: "Jeans, Cargo pants, Chinos, Shorts",
    icon: Layers,
  },
  {
    id: "Shoes",
    label: "Shoes",
    shortLabel: "Shoes",
    description: "Sneakers, Loafers, Boots, Sandals",
    icon: Footprints,
  },
  {
    id: "Accessories",
    label: "Accessories",
    shortLabel: "Accessories",
    description: "Watches, Bags, Belts, Caps",
    icon: Watch,
  },
];

export const CATEGORY_IDS = ["Upper", "Lower", "Shoes", "Accessories"];

export function getCategoryInfo(categoryId) {
  if (!categoryId) return null;
  const normalized = categoryId.toLowerCase();
  return (
    CATEGORIES.find((c) => c.id.toLowerCase() === normalized) || {
      id: categoryId,
      label: categoryId,
      shortLabel: categoryId,
      description: "",
      icon: Shirt,
    }
  );
}

export function formatCategorySlot(category) {
  const info = getCategoryInfo(category);
  return info ? info.shortLabel : "Piece";
}
