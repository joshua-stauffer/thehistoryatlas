import React from "react";
import { Box, Chip } from "@mui/material";
import { ThemeCategory } from "../../api/themes";

interface ThemeFilterProps {
  categories: ThemeCategory[];
  selectedSlugs: Set<string>;
  onToggle: (slug: string) => void;
}

export const ThemeFilter: React.FC<ThemeFilterProps> = ({
  categories,
  selectedSlugs,
  onToggle,
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        overflowX: "auto",
        py: 1.5,
        px: { xs: 1, sm: 0 },
        "&::-webkit-scrollbar": { display: "none" },
        scrollbarWidth: "none",
      }}
    >
      {categories.map((cat) => (
        <Chip
          key={cat.slug}
          label={cat.name}
          variant={selectedSlugs.size === 0 ? "filled" : "outlined"}
          size="medium"
          onClick={() => {
            // Clicking a category toggles all its children
            const childSlugs = cat.children.map((c) => c.slug);
            const allSelected = childSlugs.every((s) => selectedSlugs.has(s));
            childSlugs.forEach((s) => {
              if (allSelected || !selectedSlugs.has(s)) {
                onToggle(s);
              }
            });
          }}
          sx={{
            fontWeight: 600,
            flexShrink: 0,
            ...(cat.children.some((c) => selectedSlugs.has(c.slug)) && {
              backgroundColor: "primary.main",
              color: "white",
              "&:hover": { backgroundColor: "primary.dark" },
            }),
          }}
        />
      ))}
    </Box>
  );
};
