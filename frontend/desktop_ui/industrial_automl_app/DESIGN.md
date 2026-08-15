---
name: Industrial AutoML Intelligence
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#46464e'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76767e'
  outline-variant: '#c6c5ce'
  surface-tint: '#555d7f'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#121a38'
  on-primary-container: '#7b82a6'
  inverse-primary: '#bec5ec'
  secondary: '#765933'
  on-secondary: '#ffffff'
  secondary-container: '#fdd6a7'
  on-secondary-container: '#785c35'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#bec5ec'
  on-primary-fixed: '#121a38'
  on-primary-fixed-variant: '#3e4566'
  secondary-fixed: '#ffe866'
  secondary-fixed-dim: '#e6c200'
  on-secondary-fixed: '#291800'
  on-secondary-fixed-variant: '#5b421e'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
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
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 32px
  gutter: 24px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style

This design system is engineered for an enterprise-grade industrial AutoML platform. It balances the high-precision requirements of technical engineering with the sleek efficiency of modern SaaS. The brand personality is **Credible, Technical, and Enterprise-ready**.

The visual direction follows a **Corporate Modern** style with a focus on high-clarity information architecture. It leverages a "Light Mode" default to ensure maximum readability during long analytical sessions, punctuated by heavy, "Deep Obsidian" interactive elements that signify stability and authority. To prevent the interface from feeling cold, subtle **Industrial Glows** (radial highlights) are used to draw attention to key data insights and platform successes.

## Colors

The color palette is rooted in a professional, high-contrast foundation. 

- **Background:** A pure `#FFFFFF` is used for the primary canvas to maintain an "Industrial Lab" cleanliness.
- **Deep Obsidian (#0D1533):** This is the primary functional color. It is used for all high-emphasis text, primary navigation, and "Pill" action buttons.
- **Gold (#FFD700):** Reserved for technical highlights. Use this as a subtle radial gradient behind high-value charts or as a highlight stroke for "Active" or "Insight" states.
- **Surface Neutrals:** Use `#F8FAFC` for secondary containers to create tonal separation from the main background.
- **Borders:** Subtle `#E2E8F0` borders are the primary method of element separation, ensuring the UI feels structured rather than floating.

## Typography

The design system utilizes **Inter** across all levels to leverage its exceptional legibility and neutral, technical character. 

- **Display & Headlines:** Use tight letter-spacing and semi-bold/bold weights to create a sense of structural permanence. 
- **Data Labels:** Use the `label-sm` style for chart axes and metadata. The slight tracking (letter spacing) and medium weight ensure clarity at small sizes.
- **Readability:** Body text should maintain a generous line height (1.5x) to ensure complex technical documentation and model logs remain accessible.

## Layout & Spacing

This design system employs a **Fixed Grid** philosophy for desktop (max-width 1440px) to ensure data visualizations maintain a predictable aspect ratio.

- **Grid Model:** 12-column grid with 24px gutters. 
- **Margins:** 32px safe-area margins for dashboard views; 64px+ for landing/marketing pages.
- **Rhythm:** An 8px baseline grid governs all internal padding and vertical rhythm. 
- **Adaptation:** On mobile, the 12-column grid collapses to 4 columns. Cards that span 3 or 4 columns on desktop should reflow to full-width (4 columns) on mobile devices.

## Elevation & Depth

Visual hierarchy is achieved through a combination of **Tonal Layers** and **Soft Ambient Shadows**.

- **Level 0 (Background):** Pure white (#FFFFFF).
- **Level 1 (Cards/Containers):** White surface, 1px solid border (#E2E8F0), and a very soft, diffused shadow (0px 4px 20px rgba(13, 21, 51, 0.04)).
- **Level 2 (Dropdowns/Modals):** White surface, 1px solid border (#E2E8F0), and a more pronounced shadow (0px 12px 32px rgba(13, 21, 51, 0.08)).
- **Industrial Highlight:** For "Active" states or featured insights, a subtle inner-glow using the Gold accent color can be applied to indicate machine-learning activity.

## Shapes

The shape language is characterized by "Industrial Softness"—precision-engineered corners that feel approachable but professional.

- **Cards & Primary Containers:** Use `rounded-2xl` (1rem / 16px) to soften the enterprise data density.
- **Interactive Elements:** Buttons and tags utilize a **Pill-shaped** (full radius) geometry to contrast against the structured rectangular grid of the dashboard.
- **Inputs:** Utilize `rounded-lg` (0.5rem / 8px) to maintain a standard form-factor appearance.

## Components

### Buttons
- **Primary:** Dark Pill buttons. Background `#0D1533`, Text `#FFFFFF`. High contrast and authoritative.
- **Secondary:** Transparent background with `#0D1533` border and text.
- **Ghost:** No border, `#64748B` text, becomes `#0D1533` on hover.

### Cards
- **Structure:** `rounded-2xl` corners, `#FFFFFF` background, `#E2E8F0` subtle border.
- **Header:** Integrated title with `label-md` uppercase text for section identification.

### Input Fields
- **Default:** White background, 1px border (#E2E8F0), 8px radius. 
- **Focus:** Border shifts to `#0D1533` with a subtle 2px outer ring of `#FFD700` (Gold).

### Chips & Badges
- **Status Badges:** Pill-shaped with light background tints (e.g., light green for "Success", light amber for "Processing").
- **Technical Tags:** Small, monospaced-style Inter labels for model parameters.

### Data Visualization
- **Line/Bar Charts:** Use `#0D1533` for primary data sets. Use `#FFD700` for "Predicted" or "Optimized" data paths to highlight the AI's impact.