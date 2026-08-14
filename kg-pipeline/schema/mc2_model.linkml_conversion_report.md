# CSV -> LinkML conversion report

## Summary
- input files: 1
- attributes read: 610
- classes: 39
- slots: 572
- enums: 169
- warnings: 1

## Warnings (1)
Rows/values that need human review before the schema is trusted.

- Class 'Study' DependsOn references 'Study Number of Samples', which has no row of its own in the input — check for a typo or missing module file.

## Notes (16)
Design decisions applied automatically — verify they're right for your case.

- 'USE' has a conditional DependsOn on ['userSpecificRestriction'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'COL' has a conditional DependsOn on ['collaborationRequired'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'RST' has a conditional DependsOn on ['researchSpecificRestrictions'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'TSM' has a conditional DependsOn on ['timeLimitOnUse'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'MOR' has a conditional DependsOn on ['publicationMoratorium'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'IST' has a conditional DependsOn on ['institutionSpecificRestriction'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'GSR' has a conditional DependsOn on ['geographicalRestriction'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DSR' has a conditional DependsOn on ['diseaseSpecificResearch'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus1' has a conditional DependsOn on ['sourceGeography'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus2' has a conditional DependsOn on ['populationType'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus3' has a conditional DependsOn on ['deidentificationType'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus4' has a conditional DependsOn on ['dataPermission'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus5' has a conditional DependsOn on ['dataTier'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus6' has a conditional DependsOn on ['license'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- 'DUOPlus7' has a conditional DependsOn on ['attribution'] — consider encoding as a LinkML `rules:` entry if this must be enforced.
- '10x Visium RNA Level 1' treated as a class (DependsOn lists 37 fields) even though IsTemplate is not set — verify this is a component, not a typo.
