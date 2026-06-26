# Bundled UI fonts

All four families are licensed under the SIL Open Font License 1.1
(https://openfontlicense.org), which permits bundling and redistribution.
Fetched from the Google Fonts project (https://github.com/google/fonts/tree/main/ofl):

| Family | Files | Source |
|--------|-------|--------|
| Cormorant Garamond | `CormorantGaramond.ttf`, `CormorantGaramond-Italic.ttf` | `ofl/cormorantgaramond/` |
| Chakra Petch | `ChakraPetch-Regular/Medium/SemiBold.ttf` | `ofl/chakrapetch/` |
| Share Tech Mono | `ShareTechMono-Regular.ttf` | `ofl/sharetechmono/` |
| Saira | `Saira.ttf` (variable) | `ofl/saira/` |

Registered at startup by `docsummarizer/ui/fonts.py` so QML resolves them by
family name; bundled into the portable build by `DocSummarizer.spec`.
