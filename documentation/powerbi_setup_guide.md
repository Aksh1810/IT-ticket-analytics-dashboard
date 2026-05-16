# Power BI Setup Guide

A click-by-click guide for a beginner Power BI user. By the end you will have
a fully working IT helpdesk dashboard with all KPIs, a star-schema data model,
working slicers, and a publish-ready `.pbix` file.

> Estimated time: **30–45 minutes**.

---

## 0. Prerequisites

1. Run the data pipeline first so `data/processed/*.csv` exists:
   ```bash
   bash scripts/run_all.sh
   ```
2. Install **Power BI Desktop** (free, Windows-only).
3. Open Power BI Desktop, then **File → Save As** and save the empty file as `IT_Helpdesk_Dashboard.pbix` in your project root.

---

## 1. Import the CSV files

You will import **six** CSVs from `data/processed/`.

For each file:

1. **Home → Get Data → Text/CSV**.
2. Browse to `data/processed/` and pick one of:
   - `fact_tickets.csv`
   - `dim_agent.csv`
   - `dim_category.csv`
   - `dim_channel.csv`
   - `dim_priority.csv`
   - `dim_calendar.csv`
3. In the preview dialog, click **Transform Data**.
4. In Power Query Editor, rename the query (right pane → Properties → Name) to remove the underscores and use PascalCase:
   - `fact_tickets` → `FactTickets`
   - `dim_agent` → `DimAgent`
   - `dim_category` → `DimCategory`
   - `dim_channel` → `DimChannel`
   - `dim_priority` → `DimPriority`
   - `dim_calendar` → `DimCalendar`
5. **Home → Close & Apply** once all six queries are loaded.

---

## 2. Set column data types

Power BI may guess wrong on a few columns. Use **Modeling → Data type** (or the dropdown above each column) to set them precisely.

### FactTickets

| Column | Required Type |
|---|---|
| `ticket_id` | Text |
| `created_at` | Date/time |
| `resolved_at` | Date/time |
| `first_response_at` | Date/time |
| `status` | Text |
| `agent_key` | Whole number |
| `category_key` | Whole number |
| `channel_key` | Whole number |
| `priority_key` | Whole number |
| `created_date_key` | Whole number |
| `satisfaction_score` | Decimal number |
| `reopen_count` | Whole number |
| `resolution_hours` | Decimal number |
| `response_hours` | Decimal number |
| `sla_target_hours` | Whole number |
| `sla_breached` | Whole number |
| `is_first_contact_resolved` | Whole number |
| `ticket_age_band` | Text |

> **Important:** if `created_at` imports as Text, your relationships will break. Fix it before continuing.

### DimAgent

| Column | Type |
|---|---|
| `agent_key` | Whole number |
| `agent_name` | Text |
| `team` | Text |

### DimCategory

| Column | Type |
|---|---|
| `category_key` | Whole number |
| `category_name` | Text |

### DimChannel

| Column | Type |
|---|---|
| `channel_key` | Whole number |
| `channel_name` | Text |

### DimPriority

| Column | Type |
|---|---|
| `priority_key` | Whole number |
| `priority_name` | Text |
| `sla_target_hours` | Whole number |

### DimCalendar

| Column | Type |
|---|---|
| `date_key` | Whole number |
| `date` | Date |
| `day_of_week` | Text |
| `week_number` | Whole number |
| `month_number` | Whole number |
| `month_name` | Text |
| `quarter` | Whole number |
| `year` | Whole number |
| `is_weekend` | Whole number |
| `is_business_day` | Whole number |

---

## 3. Create the five relationships

Open **Model view** (the left-sidebar icon that looks like three connected boxes).

Drag-and-drop from FactTickets to each dim to create these relationships. For each one, **double-click the line** to verify:

- **Cardinality:** Many to one (*:1)
- **Cross filter direction:** Single
- **Make this relationship active:** ✓ checked

| From (FactTickets) | To | Cardinality | Direction |
|---|---|---|---|
| `agent_key` | `DimAgent[agent_key]` | Many-to-One | Single |
| `category_key` | `DimCategory[category_key]` | Many-to-One | Single |
| `channel_key` | `DimChannel[channel_key]` | Many-to-One | Single |
| `priority_key` | `DimPriority[priority_key]` | Many-to-One | Single |
| `created_date_key` | `DimCalendar[date_key]` | Many-to-One | Single |

---

## 4. Mark DimCalendar as a Date Table

1. In **Model view**, click `DimCalendar`.
2. **Table tools → Mark as date table → Mark as date table**.
3. In the dialog, choose the `date` column.
4. Click **OK**.

(Power BI's time-intelligence DAX functions require this step.)

---

## 5. Create the `_Measures` table

1. **Home → Enter Data**.
2. Leave the grid empty. Set the table name to `_Measures`. Click **Load**.
3. In the Fields pane, expand `_Measures`. Right-click the auto-generated `Column1` and **Hide in report view**.

(Naming it with a leading underscore floats it to the top of the Fields pane.)

---

## 6. Paste DAX measures

Open `measures/all_measures.dax` in any text editor. For **each measure** in that file:

1. Click on the `_Measures` table in the Fields pane.
2. **Home → New measure**.
3. Replace the default formula bar text with the entire measure (including the `[Name] :=` line — Power BI will accept it).
4. Press **Enter** or click the checkmark.
5. With the new measure selected, set its **Home format** in the ribbon:
   - `*Rate` and `*Display` ending in `%` → no special format (they are text).
   - `*Hours`, `Avg CSAT`, etc. → 1 decimal place.
   - Count measures → Whole number, thousands separator.

Repeat for all measures. There are ~30. It is tedious but a one-time setup.

---

## 7. Build the visuals

### Page 1 — Overview (executive KPI page)

#### 7.1 KPI cards row (top of page)

Insert **five Card** visuals (Visualizations pane → Card). For each card, drag a single measure to the **Fields** well.

| Card | Measure | Format |
|---|---|---|
| Total Tickets | `[Total Tickets]` | Whole number |
| Open Backlog | `[Backlog Count]` | Whole number |
| MTTR | `[MTTR Display]` | Text |
| SLA Compliance | `[SLA Compliance Display]` | Text |
| CSAT | `[CSAT Display]` | Text |

**Conditional formatting on Total Tickets:** Format → Callout value → Color → fx → Format style "Rules":
- < 100 = green
- 100–500 = orange
- > 500 = red

**Conditional formatting on SLA Compliance:** apply Rules on `[SLA Compliance Rate]`:
- ≥ 95 = green
- 85–94.99 = orange
- < 85 = red

#### 7.2 Tickets by Day line chart

- Visual: **Line chart**.
- X-axis: `DimCalendar[date]`
- Y-axis: `[Total Tickets]`
- Sort: ascending by date.

#### 7.3 Tickets by Priority bar chart

- Visual: **Clustered bar chart**.
- Y-axis: `DimPriority[priority_name]`
- X-axis: `[Total Tickets]`
- Sort: by `[Total Tickets]` descending.
- Data colors: Critical=red, High=orange, Medium=blue, Low=gray.

#### 7.4 Aging breakdown donut

- Visual: **Donut chart**.
- Legend: `FactTickets[ticket_age_band]`
- Values: `[Total Tickets]`
- Filter: `ticket_age_band <> "(Resolved)"` (drag the field to the visual filter pane).

### Page 2 — SLA & Performance

- KPI cards: `[SLA Breach Count]`, `[SLA At Risk]`, `[FCR Rate Display]`, `[Oldest Open Ticket Days]`.
- **Matrix** visual:
  - Rows: `DimAgent[agent_name]`
  - Values: `[Total Tickets]`, `[Agent MTTR]`, `[Agent FCR Rate]`, `[Agent SLA Compliance]`
  - Sort: `[Agent SLA Compliance]` ascending (worst at top).
  - Conditional formatting on `Agent SLA Compliance`: Format → Cell elements → Background color → Rules: <80=red, 80–94=orange, ≥95=green.
- **Clustered column chart** (SLA breach by category):
  - X-axis: `DimCategory[category_name]`
  - Y-axis: `[SLA Breach Rate by Category]`
  - Sort descending.

### Page 3 — CSAT

- Cards: `[CSAT Display]`, `[CSAT Satisfied Rate]`, `[CSAT Dissatisfied Rate]`.
- **Stacked bar** by category showing satisfied / neutral / dissatisfied splits.

---

## 8. Slicers

On every page, add slicers at the top:

| Slicer | Field | Mode |
|---|---|---|
| Date range | `DimCalendar[date]` | **Between** (relative date) |
| Priority | `DimPriority[priority_name]` | Vertical list |
| Team | `DimAgent[team]` | Dropdown |
| Channel | `DimChannel[channel_name]` | Dropdown |

**Sync slicers across pages:**

1. **View → Sync slicers**.
2. Select each slicer in turn; in the Sync slicers pane, tick both **Sync** and **Visible** for every page.

---

## 9. Page navigation buttons

1. **Insert → Buttons → Blank**. Repeat for as many pages as you have (3).
2. With a button selected, in Format pane → **Action → On → Type = Page navigation → Destination = (page name)**.
3. Set the button text to the page name.
4. Hold **Ctrl** to test-click in design mode.
5. Group the buttons (**Shift-click + Group**) and copy/paste onto every page in the same position so the nav looks identical.

---

## 10. Publish to Power BI Service

1. **Home → Publish**. Sign in with your Microsoft account.
2. Choose a workspace (My workspace is fine for a portfolio).
3. After upload, click **Open in Power BI** to view the report online.
4. Optional: **File → Export → Export to PDF** for a static portfolio snapshot.

> **Refreshing data:** because we used local CSVs, scheduled refresh requires a personal gateway. For a portfolio, "manually re-publish after running the Python pipeline" is fine.
