---
name: Biblio Design System
colors:
  surface: '#fbf9fb'
  surface-dim: '#dbd9db'
  surface-bright: '#fbf9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f5'
  surface-container: '#efedef'
  surface-container-high: '#eae7ea'
  surface-container-highest: '#e4e2e4'
  on-surface: '#1b1b1d'
  on-surface-variant: '#44474d'
  inverse-surface: '#303032'
  inverse-on-surface: '#f2f0f2'
  outline: '#75777e'
  outline-variant: '#c5c6cd'
  surface-tint: '#515f78'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#0d1c32'
  on-primary-container: '#76849f'
  inverse-primary: '#b9c7e4'
  secondary: '#5e5e5c'
  on-secondary: '#ffffff'
  secondary-container: '#e1dfdc'
  on-secondary-container: '#636360'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#2b1701'
  on-tertiary-container: '#9f7d5b'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#b9c7e4'
  on-primary-fixed: '#0d1c32'
  on-primary-fixed-variant: '#39475f'
  secondary-fixed: '#e4e2de'
  secondary-fixed-dim: '#c8c6c3'
  on-secondary-fixed: '#1b1c1a'
  on-secondary-fixed-variant: '#474744'
  tertiary-fixed: '#ffdcbd'
  tertiary-fixed-dim: '#e7bf99'
  on-tertiary-fixed: '#2b1701'
  on-tertiary-fixed-variant: '#5d4124'
  background: '#fbf9fb'
  on-background: '#1b1b1d'
  surface-variant: '#e4e2e4'
  sage-green: '#8A9A5B'
  antique-gold: '#C5A059'
  ink-blue: '#112240'
  paper-shadow: '#E8E4D9'
  alert-crimson: '#93272C'
typography:
  display-lg:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Playfair Display
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1200px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 20px
---

## Brand & Style

The design system is crafted for a digital library environment that bridges the gap between traditional academic prestige and modern functional efficiency. The brand personality is **scholarly, trustworthy, and serene**, aiming to evoke the quiet focus of a physical reading room while providing the speed of a contemporary SaaS application.

The primary design style is **Modern Corporate with a Tactile Academic twist**. It utilizes a sophisticated "Warm Minimalism" approach—heavy on purposeful whitespace and high-quality typography, but grounded by rich, traditional colors and subtle textures. 

### Visual Pillars:
*   **Academic Heritage:** High-contrast serif headings and a palette inspired by leather-bound books and aged parchment.
*   **Contemporary Utility:** A rigid, functional grid and clean sans-serif body text to ensure data density remains readable for librarians.
*   **Tactile Sophistication:** Subtle use of depth and book-spine motifs to provide a sense of physical presence without the clutter of traditional skeuomorphism.

## Colors

The palette is rooted in a high-contrast relationship between **Dark Navy (Midnight Ink)** and **Warm Cream (Aged Paper)**. This combination ensures maximum legibility while maintaining a "warm" academic feel that is easier on the eyes than pure black and white.

*   **Primary (#0A192F):** Used for navigation backgrounds, primary headings, and high-emphasis UI elements. It represents authority and stability.
*   **Secondary/Surface (#FDFBF7):** The main background color for all screens. It provides a soft, paper-like canvas.
*   **Sage Green (#8A9A5B):** Utilized for positive actions, "Available" status indicators, and success states. It adds a natural, botanical calmness.
*   **Antique Gold (#C5A059):** Reserved for highlights, special UI accents (like bookmarks or featured books), and "Pustakawan" specific administrative actions.
*   **Alert Crimson:** A deep red used sparingly for overdue notices and system errors, maintaining the serious academic tone.

## Typography

The typographic strategy relies on a classic **Serif/Sans-Serif pairing**. 

**Playfair Display** is the "voice" of the library, used for all major headings and titles to evoke the feel of editorial publishing and historical archives. Its high contrast and elegant serifs should be given plenty of room to breathe.

**Inter** handles the "workforce" duties. It is used for all body text, data tables, and interface controls. This ensures that even when managing dense catalogs or complex loan transactions, the information remains perfectly legible and modern.

*   Use **Label-MD** (uppercase with tracking) for section headers and table headers to provide a clear structural hierarchy.
*   Maintain a generous line height for body text to improve readability during long sessions of catalog browsing.

## Layout & Spacing

The design system employs a **Fixed Grid** approach for desktop to mirror the structured nature of a library bookshelf, while transitioning to a **Fluid Grid** for mobile devices.

### Grid System
*   **Desktop:** 12-column grid with a maximum width of 1200px. Content is centered with 40px outer margins.
*   **Tablet:** 8-column grid with 32px margins.
*   **Mobile:** 4-column grid with 20px margins.

### Spacing Rhythm
A 8px base unit (linear scale) governs all padding and margins. 
*   **Page Sections:** 64px or 80px vertical spacing.
*   **Component Grouping:** 24px or 32px.
*   **Internal Component Padding:** 12px or 16px.

Large amounts of whitespace should be used around book titles and search results to prevent the "cluttered database" look typical of older library systems.

## Elevation & Depth

To maintain the "warm academic" aesthetic, the design system avoids heavy, tech-focused shadows. Instead, it uses **Tonal Layering** and **Subtle Materiality**.

*   **Surface Levels:** The primary background is the warm cream `Secondary`. Cards and containers use a slightly lighter version or a 1px border of `Paper-Shadow`.
*   **Shadows:** When necessary for floating elements (like modals or dropdowns), shadows should be extremely soft, using the `Primary` color at 5-10% opacity with a large blur radius (20px+) to simulate natural ambient light.
*   **The "Book Edge":** For book covers in the catalog, use a 1px inner border on the left side to simulate a book spine, adding a subtle 3D effect without needing complex gradients.
*   **Backdrop:** On large screens, the area outside the main container can feature a very subtle, low-contrast botanical watermark or a vertical line pattern reminiscent of book pages.

## Shapes

The shape language is **Soft and Precise**. 

We avoid the "bubbly" look of fully rounded UI elements to maintain a professional, academic tone. A **Soft (4px)** radius is the standard for most components. This provides just enough friendliness to feel modern while maintaining the architectural structure of a formal institution.

*   **Inputs & Buttons:** 4px radius.
*   **Cards:** 8px (Large) radius for a slightly softer container feel.
*   **Status Tags:** 2px or 4px radius (avoid pill shapes unless used for user avatars).

## Components

### Buttons
*   **Primary:** Solid `Primary` (Navy) with `Secondary` (Cream) text. 4px radius.
*   **Secondary:** `Antique Gold` or `Sage Green` with white text for specific calls to action (e.g., "Pinjam" or "Setujui").
*   **Ghost:** Transparent background with `Primary` border and text. Used for "Cancel" or "View Details."

### Cards (The "Book" Component)
Cards are the heart of the catalog. They should feature:
*   A clear image ratio for book covers (2:3).
*   Title in `Headline-SM` (Serif).
*   Author in `Body-SM` (Sans-Serif).
*   A subtle 1px border (`Paper-Shadow`) instead of a heavy shadow.

### Status Indicators
*   **Available:** Sage Green background with dark green text.
*   **Borrowed/Reserved:** Navy background with cream text.
*   **Overdue:** Alert Crimson background with white text.

### Input Fields
Inputs should mimic a "fill-in-the-blank" form feel:
*   Bottom border only or a very light 4-sided border in `Paper-Shadow`.
*   Focus state: Border changes to `Antique Gold` with a very soft outer glow.
*   Labels always visible above the input in `Label-SM`.

### Tables (Librarian Dashboard)
*   Clean, minimalist headers using `Label-MD`.
*   Striped rows using a 3% opacity of the `Primary` color for the alternating row.
*   Action buttons should be icon-only or small labels to maximize data density.