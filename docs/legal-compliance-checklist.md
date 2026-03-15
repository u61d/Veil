# Veil Legal And Compliance Checklist

This is a technical redistribution checklist, not legal advice.

## Branding and trademark hygiene

- Do not ship Mozilla or Firefox names, logos, or other protected branding for a modified redistribution.
- Use Veil-specific product name, display name, package names, icons, and artwork.
- Review all branding-specific update URLs, support URLs, welcome pages, and release metadata.
- Verify modified builds do not present themselves as official Firefox.
- Keep a record of every remaining upstream branding string that must be replaced.

## Licensing and source publication

- Preserve upstream source headers and license notices.
- Keep the MPL 2.0 license text and any required third-party notices in redistributed source and binaries.
- Publish the corresponding modified source for distributed Veil binaries.
- Track third-party license obligations introduced by any new assets or dependencies.

## Distribution checks

- Replace or document application identifiers, package metadata, and installer strings.
- Ensure update infrastructure, if any, points to Veil-controlled endpoints.
- Verify source-offer and notice requirements for release artifacts.
- Review whether crash reporting, telemetry, or remote services send data to third parties by default.

## When counsel is wise

- before the first public binary redistribution
- before shipping new branding assets derived from Mozilla artwork
- before using any wording that could imply official Mozilla endorsement
