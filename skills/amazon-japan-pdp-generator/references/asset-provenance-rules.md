# Asset Provenance Rules

## Purpose

Asset existence, source verification and publication authorization are separate decisions. The Resolver must never upgrade a file to official merely because a path resolves.

## Canonical source types

- `official`: user-provided official Product/marketing asset with verified origin.
- `user_supplied`: provided by the user but not yet verified as official or authorized.
- `generated_scene`: AI-generated scene/background without a product body.
- `placeholder`: layout-only temporary asset.
- `external_reference`: downloaded/reference-only material not cleared for production.
- `unknown`: provenance cannot be determined.

Every record carries `source_type`, `source_path`, `verification_status`, `product_layer_allowed`, `resolved`, `file_resolved`, `source_verified` and `usage_approved`.

## Independent checks

- `file_resolved`: the referenced file is accessible.
- `source_verified`: origin has been verified against the project source record.
- `usage_approved`: channel/use authorization is approved.
- `product_layer_allowed`: true only when all Product Layer rules pass.

`resolved` is a compatibility alias for path resolution only. It is never evidence of source or usage approval.

## Product Layer hard gate

Product Layer requires all of:

1. `source_type = official`;
2. `source_origin = User Provided Official`;
3. allowed official asset type;
4. `product_body_ai_generated = false`;
5. `file_resolved = true`;
6. `source_verified = true`;
7. `usage_approved = true`.

`placeholder`, `external_reference`, `generated_scene` and `unknown` are always forbidden as Product Layer. A `user_supplied` item remains blocked until official origin and usage authorization are verified. Generated scenes may be used only as Scene Layer and may not contain or reconstruct the product body, logo, Japanese text, UI or technical labels.

## Failure behavior

Any Product Layer provenance failure blocks Publish Gate. Review and design artifacts may still be produced, but `final/` and `export/` remain absent. The failure must remain visible in Asset Resolver, Design Review and reports.
