---
name: 'Blueprint Tactical: Jane Edition'
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c5c9b0'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8f937c'
  outline-variant: '#454936'
  surface-tint: '#b3d338'
  primary: '#ffffff'
  on-primary: '#2a3500'
  primary-container: '#cff053'
  on-primary-container: '#586c00'
  inverse-primary: '#536600'
  secondary: '#b0c6ff'
  on-secondary: '#002d6f'
  secondary-container: '#006df7'
  on-secondary-container: '#fefcff'
  tertiary: '#ffffff'
  on-tertiary: '#620042'
  tertiary-container: '#ffd8e8'
  on-tertiary-container: '#b52681'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#cff053'
  primary-fixed-dim: '#b3d338'
  on-primary-fixed: '#171e00'
  on-primary-fixed-variant: '#3e4c00'
  secondary-fixed: '#d9e2ff'
  secondary-fixed-dim: '#b0c6ff'
  on-secondary-fixed: '#001945'
  on-secondary-fixed-variant: '#00429b'
  tertiary-fixed: '#ffd8e8'
  tertiary-fixed-dim: '#ffafd5'
  on-tertiary-fixed: '#3d0027'
  on-tertiary-fixed-variant: '#8a005f'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
  background-pitch: '#000000'
  surface-slate: '#16181c'
  intent-clarification: '#ffb900'
  action-proposed: '#00f0ff'
  assistant-identity: '#d4f658'
  grid-line: '#2a2d32'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.03em
  headline-md:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.02em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: 0.1em
  assistant-msg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-safe: 32px
  chat-gap: 16px
  docked-width: 380px
---

## Brand & Style

This design system evolves the "Schematic Minimalist" philosophy into a high-functioning AI interface. The brand personality is defined by surgical precision, transparency, and a "glass-box" approach to artificial intelligence—where the assistant's logic is as visible as its output. 

The aesthetic is **Dark-Mode-First High-Contrast**, blending technical brutalism with sophisticated motion. It targets power users who require an AI that feels less like a chatbot and more like a tactical co-pilot. The emotional response is one of absolute control, technical mastery, and futuristic efficiency.

## Colors

The system is optimized for deep-blacks and neon-phosphor interactions.

- **Assistant States:** 
  - **Jane Identity:** Uses the signature `#d4f658` (Neon Lime) for her presence, avatar pulses, and "thinking" states.
  - **Intent Clarification:** A warm, high-visibility amber (`#ffb900`) triggers when the system requires user confirmation or identifies ambiguity.
  - **Action Proposed:** A vibrant blueprint-blue/cyan (`#00f0ff`) highlights suggested automations or executable code blocks.
- **Backgrounds:** Use `#000000` (Pitch Black) for the primary canvas to maximize the "infinite space" feel, with `#121212` for docked panels.

## Typography

The dual-font system maintains strict separation between narrative and technical data. 

**JetBrains Mono** is utilized for all system-generated "meta-talk," timestamps, and code blocks. **Inter** handles user prompts and the assistant’s primary responses. In the chat context, assistant messages use a slightly tighter line-height (`assistant-msg`) to allow for better information density in complex technical exchanges.

## Layout & Spacing

This design system uses a **Fixed Grid** with contextual side-panels for the AI assistant.

- **Docked State:** The assistant resides in a fixed right-side panel (380px) with a persistent 1px border.
- **Expanded State:** Transitions via a "technical slide" where the main content area compresses horizontally to accommodate the assistant, rather than the assistant overlaying the content.
- **Chat Rhythm:** Use a 16px vertical gap between message clusters. Individual messages within a cluster use 4px spacing.

## Elevation & Depth

Hierarchy is established through **Luminance and Outlines**.

- **Technical Grid:** A background grid of subtle 1px dots (`#2a2d32`) is always visible, serving as the floor for all elements.
- **Layering:** The assistant's chat container uses a slightly higher luminance background (`#16181c`) than the main canvas (`#000000`).
- **Neon Glows:** Avoid standard shadows. Instead, use a very subtle, 4px blur "outer glow" in the color of the assistant's current state (Lime, Amber, or Cyan) to indicate active focus or processing.

## Shapes

The "Binary Contrast" rule applies:
- **Messages & Action Cards:** Soft corners (4px) provide enough distinction from the sharp 0px background grid.
- **Buttons & Avatar:** Full Pill (rounded-full) shape. The assistant's avatar should be a circular ring that pulses with neon intensity.

## Components

### Chat Bubbles
- **User Messages:** Right-aligned, no background, 1px border (`#2a2d32`), white text.
- **Assistant Messages:** Left-aligned, no background. The message is preceded by a vertical 2px "status line" in the current state color (e.g., Neon Lime).

### Action Cards
- Used for "Action Proposed" states. These feature a 1px Cyan border, a `label-mono` header, and a primary pill button. The card background should have a 5% Cyan tint to differentiate it from standard text.

### Assistant Input
- A persistent bar at the bottom of the assistant panel. It features no background, a 1px top-border, and a monospace "READY_FOR_INPUT" prompt as a placeholder.

### Transitions
- **Docked to Expanded:** Use a linear, high-speed slide (200ms) with a slight "rebound" to mimic the feeling of mechanical hardware components locking into place.