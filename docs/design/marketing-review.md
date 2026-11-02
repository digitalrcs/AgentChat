# Marketing design review

The page uses two image-generated design references: `marketing-hero-concept.png` and `marketing-sections-concept.png`. These are design concepts, not product screenshots. The illustration in the implemented page is explicitly labeled as an example conversation.

## Implementation comparison

| Reference decision | Implementation and review |
|---|---|
| White editorial surface, navy serif display text, restrained teal actions | Preserved using local system fonts; no third-party font or tracking request |
| Two-column hero with conversation illustration | Preserved at desktop width; stacks in reading order on mobile |
| Three open feature columns and numbered workflow | Preserved with thin separators and native SVG icons |
| Pale installation band and two-column expectations area | Preserved, stacking on a phone |
| Two linked conversation bubbles | Original SVG assets in branding/; readable light/dark wordmarks and favicon |

The concept's wording and section order are retained. Intentional differences: original vector wordmark colors, simpler decorative bullets in the expectations list, system-font line wrapping, and an independence/hosting clarification below the footer. The desktop headline retains three lines but wraps at different words from the concept. These differences avoid image text assets and keep real text selectable and responsive.

## Verification

Rendered through the in-app browser at 1536×1024 and 390×844. Saved full-page screenshots: `marketing-desktop.png`, `marketing-mobile.png`. Both were opened and visually compared with the concept images. Page scroll width matched viewport width at both sizes; the logo loaded; browser console reported no warning or error messages. Navigation to the workflow updates the expected fragment. Local Markdown links in the public guide set resolved on disk, and the documents were checked for private machine paths and LAN addresses.

Public GitHub release and Pages availability are deployment checks handled after the repository is published. This local review does not assert that those endpoints were already live.
