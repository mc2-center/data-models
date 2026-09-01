# CSV -> LinkML conversion report

## Summary
- input files: 1
- attributes read: 612
- classes: 39
- slots: 574
- enums: 171
- warnings: 1

## Warnings (1)
Rows/values that need human review before the schema is trusted.

- Class 'Study' DependsOn references 'Study Number of Samples', which has no row of its own in the input — check for a typo or missing module file.

## Notes (16)
Design decisions applied automatically — verify they're right for your case.

- 'DUO:0000026' has a conditional DependsOn on ['userSpecificRestriction'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000020' has a conditional DependsOn on ['collaborationRequired'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000012' has a conditional DependsOn on ['researchSpecificRestrictions'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000025' has a conditional DependsOn on ['timeLimitOnUse'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000024' has a conditional DependsOn on ['publicationMoratorium'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000028' has a conditional DependsOn on ['institutionSpecificRestriction'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000022' has a conditional DependsOn on ['geographicalRestriction'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUO:0000007' has a conditional DependsOn on ['diseaseSpecificResearch'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus1' has a conditional DependsOn on ['sourceGeography'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus2' has a conditional DependsOn on ['populationType'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus3' has a conditional DependsOn on ['deidentificationType'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus4' has a conditional DependsOn on ['dataPermission'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus5' has a conditional DependsOn on ['dataTier'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus6' has a conditional DependsOn on ['license'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus7' has a conditional DependsOn on ['attribution'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- '10x Visium RNA Level 1' treated as a class (DependsOn lists 39 fields) even though IsTemplate is not set — verify this is a component, not a typo.
