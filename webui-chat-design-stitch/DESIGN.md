# Design System Strategy: The Synthetic Editorial

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Synthetic Architect."** 

We are moving away from the "chat bubble" tropes of 2010s messaging apps. Instead, we are building a high-end, editorial workspace where the precision of a terminal meets the fluid beauty of glass. This system treats AI interaction not as a simple text exchange, but as a sophisticated data-orchestration event. 

By leveraging **intentional asymmetry**, we break the rigid box-model grid. Use the sidebar to anchor the layout, but allow the main chat area to breathe with expansive margins. Overlap glass panels onto dark, deep backgrounds to create a sense of physical space. The goal is a "Hacker-Chic" aesthetic: high-contrast typography, glowing accents, and tonal depth that feels expensive and intentional.

---

## 2. Colors & Surface Philosophy
The palette is grounded in the deep obsidian of `surface` (#131318), accented by the hyper-reactive greens of the `primary` scale and the electric violets of the `secondary` scale.

*   **The "No-Line" Rule:** Do not use 1px solid borders to separate the chat history from the main feed. Boundaries are defined by tonal shifts. For example, the sidebar should use `surface_container_low`, while the main workspace uses `surface`.
*   **Surface Hierarchy & Nesting:** Treat the UI as layers of data. 
    *   **Base:** `surface` (#131318).
    *   **Primary Containers:** `surface_container` (#1f1f25) for message blocks.
    *   **Elevated Details:** `surface_container_highest` (#35343a) for active states or hover effects.
*   **The "Glass & Gradient" Rule:** To achieve the "Cyberpunk" glow, use `primary_container` (#00ff41) with a low-opacity blur as a background glow behind specific UI elements. Use mesh gradients that transition from `primary_fixed_dim` (#00e639) to `secondary_container` (#cf5cff) to simulate a digital light source.
*   **Signature Textures:** For high-end "Hacker" aesthetics, apply a subtle noise texture over `surface` to eliminate flat digital gradients and provide a film-grain, analog feel.

---

## 3. Typography: The Editorial Contrast
We use a dual-font strategy to balance human readability with machine precision.

*   **Display & Headlines:** `spaceGrotesk` is our voice of authority. Use `display-lg` (3.5rem) for landing states and `headline-md` (1.75rem) for section headers. Its geometric, slightly "tech" feel aligns with the Retro-Futuristic theme.
*   **Body & Utility:** `manrope` provides the human-centric legibility required for long AI responses. Use `body-lg` (1rem) for the main chat text to ensure a comfortable reading experience.
*   **Terminal Elements:** Use `label-md` for metadata (timestamps, token counts) to evoke the "Hacker" aesthetic.
*   **Hierarchy:** High contrast is key. Pair a `label-sm` in `primary_fixed` (all caps) with a `headline-lg` in `on_surface` to create a sophisticated, editorial header.

---

## 4. Elevation, Depth & Light
Hierarchy is achieved through **Tonal Layering** and light simulation, not structural lines.

*   **The Layering Principle:** Place a `surface_container_low` sidebar next to a `surface` main area. The depth is felt, not seen through a line.
*   **Ambient Shadows:** For floating glass panels, use shadows with a blur of `24px` and an opacity of `6%` using the `on_secondary` (#520071) tint to create a "Neon Glow" instead of a muddy grey shadow.
*   **The "Ghost Border" Fallback:** If a container needs definition against a complex background (like a mesh gradient), use `outline_variant` (#3b4b37) at **15% opacity**. This provides a "holographic" edge rather than a hard boundary.
*   **Glassmorphism:** For the "Specialized Input Field," use a background of `surface_container` at 60% opacity with a `backdrop-filter: blur(12px)`. This makes the input feel like it is floating above the chat history.

---

## 5. Components

### The Intelligence Input (Input Field)
*   **Style:** A glassmorphic bar. No hard borders.
*   **State:** When active, the "Ghost Border" glows with `primary_fixed_dim` (#00e639).
*   **Typography:** User input should be `body-lg`.

### Message Nodes (Cards & Lists)
*   **Constraint:** Forbid the use of divider lines between messages. Use `spacing-6` (2rem) of vertical space to separate AI and User turns.
*   **AI Responses:** Use `surface_container_low` with a subtle `primary` glow at the top-left corner to denote "active processing."
*   **User Messages:** Subtle `surface_container_high` alignment to the right, keeping the layout asymmetric.

### Action Chips
*   **Visuals:** Use `secondary_container` (#cf5cff) for high-priority AI suggestions.
*   **Shape:** `rounded-full` for a soft contrast against the brutalist typography.

### Primary Buttons
*   **Hacker Variant:** Rectangular (`rounded-sm`), using `primary_container` text on a `surface_container_highest` background with a `primary` glow on hover.
*   **Glass Variant:** `surface_bright` with 40% opacity and a high `backdrop-blur`.

---

## 6. Do's and Don'ts

### Do
*   **DO** use whitespace as a structural element. A `spacing-12` (4rem) gutter between the sidebar and chat creates a premium, airy feel.
*   **DO** mix font weights. Pair a `label-sm` (Bold) with a `body-md` (Light) for data metadata.
*   **DO** use "Primary Glow" sparingly—only for the most important interactive elements.

### Don't
*   **DON'T** use 100% opaque borders. It kills the "Synthetic" aesthetic and makes the UI look like a legacy bootstrap template.
*   **DON'T** use pure black (#000000). Always use `surface` (#131318) to allow for depth and shadow visibility.
*   **DON'T** crowd the input field. The AI Chat is about the conversation; give the text room to breathe.