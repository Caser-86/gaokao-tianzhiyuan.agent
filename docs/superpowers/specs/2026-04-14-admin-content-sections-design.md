# Admin Content Sections Design

## Goal

Add admin-side editing for school and major `sections` so operations can maintain正文内容 without editing `data/catalog.json` by hand.

This first version should support:

- listing current sections for schools and majors
- editing existing sections
- adding new sections
- removing sections by submitting them as blank

This version will not support:

- drag-and-drop reordering
- rich text
- section templates
- partial autosave

## Data Shape

The existing catalog section structure stays unchanged:

```json
{
  "type": "highlights",
  "title": "学校亮点",
  "items": [
    "建筑、土木、电子科学与技术长期强势。"
  ]
}
```

Each section has:

- `type: string`
- `title: string`
- `items: string[]`

The admin feature will continue using this shape directly.

## Admin API

Add three endpoints:

- `GET /api/admin/content-sections`
- `POST /api/admin/content-sections/schools/{slug}`
- `POST /api/admin/content-sections/majors/{slug}`

Response payload for list:

```json
{
  "schools": [
    {
      "slug": "southeast-university",
      "name": "东南大学",
      "sections": [
        {
          "type": "highlights",
          "title": "学校亮点",
          "items": ["..."]
        }
      ]
    }
  ],
  "majors": []
}
```

Update request payload:

```json
{
  "sections": [
    {
      "type": "highlights",
      "title": "学校亮点",
      "items": ["..."]
    }
  ]
}
```

## Validation Rules

- fully blank sections are ignored on save
- `type` must be non-empty if a section is submitted
- `title` must be non-empty if a section is submitted
- `items` must contain at least one non-empty line if a section is submitted
- partially filled sections return `422`
- unknown slug returns `404`

This allows simple delete behavior: clear the whole section and save.

## Admin UI

Add two new admin sections:

- `学校正文编辑`
- `专业正文编辑`

Each entity renders a form containing:

- hidden `slug`
- entity name
- entity slug
- one fieldset per existing section
- one extra blank fieldset for adding a new section

Each fieldset contains:

- `type` input
- `title` input
- `items` textarea, one item per line

Submit button text:

- `保存正文`

## Form Semantics

The UI does not need explicit add/remove buttons in this first version.

Instead:

- existing sections are shown in order
- one extra blank section row is appended
- completely blank rows are dropped when parsing form data
- clearing an existing row removes it from saved output

This keeps the feature simple and avoids client-side section state management.

## Web Data Layer

Add a new admin web client module:

- `apps/web/lib/admin-content-sections-api.ts`

It should expose:

- `listContentSections()`
- `updateSchoolSections(slug, sections)`
- `updateMajorSections(slug, sections)`

Add matching server actions in:

- `apps/web/app/(admin)/admin/actions.ts`

These actions should:

- parse submitted section rows
- skip fully blank rows
- reject partial rows
- call the admin API
- revalidate `/admin`
- revalidate `/`
- revalidate affected detail route

## Page Integration

`apps/web/app/(admin)/admin/page.tsx` should fetch content sections alongside:

- review queue
- featured content
- ranking references
- content summaries

`DashboardShell` should receive:

- `sectionSchools`
- `sectionMajors`
- `contentSectionError`
- `updateSchoolSectionsAction`
- `updateMajorSectionsAction`

## Testing

### API

Add failing tests first for:

- listing content sections
- updating school sections
- rejecting partially filled sections

### Web

Add failing tests first for:

- rendering `学校正文编辑`
- rendering `专业正文编辑`
- showing current section type, title, and items
- showing `保存正文`

Update existing admin page tests so new data dependency is mocked by default.

## Rollout

This feature should land in two commits:

- API commit for new content-sections endpoints
- Web commit for admin integration
