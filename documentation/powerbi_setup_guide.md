# Power BI Setup Guide (Web — app.powerbi.com)

A click-by-click guide using **Power BI Service** (the browser version at
[app.powerbi.com](https://app.powerbi.com)). No desktop app needed.

> Estimated time: **40–55 minutes**.

---

## 0. Prerequisites

1. Run the data pipeline first so `data/processed/*.csv` exists:
   ```bash
   bash scripts/run_all.sh
   ```
   You need all six files:
   `fact_tickets.csv`, `dim_agent.csv`, `dim_category.csv`,
   `dim_channel.csv`, `dim_priority.csv`, `dim_calendar.csv`

2. Sign in to [app.powerbi.com](https://app.powerbi.com) with your Microsoft
   account (free account works; some features require Pro/Premium — noted where relevant).

---

## 1. Create a workspace

1. In the left sidebar, click **Workspaces → + New workspace**.
2. Name it `IT Helpdesk Analytics`. Click **Apply**.

(You can also use **My workspace** if you prefer.)

---

## 2. Upload the CSVs and create the dataset

Power BI Service can build a multi-table dataset from local files inside the
report editor. Here is the exact flow:

1. From your workspace, click **+ New → Report**.
2. On the "Add data to your report" screen, click **Upload a file** if shown, OR choose **Get data** from the top ribbon.
3. **Get data → Text/CSV → Browse**.
4. Navigate to `data/processed/` and select **`fact_tickets.csv`**.
5. In the preview dialog, click **Transform data** (opens the Power Query editor in the browser).

### Inside the Power Query editor

Repeat for all six CSVs:

1. **Home → New Source → Text/CSV** and add the next CSV.
2. After adding all six, rename each query in the left pane (right-click the
   query name → **Rename**):

   | Original name | Rename to |
   |---|---|
   | `fact_tickets` | `FactTickets` |
   | `dim_agent` | `DimAgent` |
   | `dim_category` | `DimCategory` |
   | `dim_channel` | `DimChannel` |
   | `dim_priority` | `DimPriority` |
   | `dim_calendar` | `DimCalendar` |

3. Click **Home → Close & Apply**.

> **Tip:** If the browser Power Query is not available in your account tier,
> an alternative is to combine all six CSVs into one Excel workbook (each CSV
> as a separate sheet) and upload the `.xlsx` instead.

---

## 3. Set column data types

In the report view, click **Model** in the left sidebar, then click each table
and set the data types column by column using the **Properties** panel on the right.

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

> **Important:** if `created_at` shows as Text, all time-based visuals will
> break. Fix the type before continuing.

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

## 4. Create the five relationships

1. In the left sidebar, click the **Model view** icon (looks like three connected boxes).
2. You will see all six tables as cards. Drag a column from FactTickets onto the
   matching column in the dim table to create a relationship line.
3. **Double-click each line** to confirm the settings:
   - **Cardinality:** Many to one (*:1)
   - **Cross filter direction:** Single
   - **Make this relationship active:** checked

Create these five relationships:

| From (FactTickets column) | To table → column | Cardinality |
|---|---|---|
| `agent_key` | DimAgent → `agent_key` | Many-to-One |
| `category_key` | DimCategory → `category_key` | Many-to-One |
| `channel_key` | DimChannel → `channel_key` | Many-to-One |
| `priority_key` | DimPriority → `priority_key` | Many-to-One |
| `created_date_key` | DimCalendar → `date_key` | Many-to-One |

---

## 5. Mark DimCalendar as a Date Table

1. In **Model view**, click the `DimCalendar` table card.
2. In the top ribbon, click **Table tools → Mark as date table**.
3. In the dialog, set the date column to `date`.
4. Click **OK**.

This enables Power BI's time-intelligence functions (DATESINPERIOD, etc.) used
by some DAX measures.

---

## 6. Create the `_Measures` table

1. In the report editor, click **Home → Enter data** (top ribbon).
2. Leave the single cell blank. Set the table name to `_Measures`.
3. Click **Load**.
4. In the **Data** pane on the right, expand `_Measures`.
5. Right-click `Column1` → **Hide**.

> The leading underscore makes `_Measures` sort to the top of the Data pane.

---

## 7. Paste DAX measures

Open `measures/all_measures.dax` in any text editor (Notepad, VS Code, etc.).

For **each measure** in that file:

1. In the Data pane, click on `_Measures` to select it.
2. In the top ribbon, click **Home → New measure**.
3. The formula bar appears. Delete the default text and paste the full measure:
   ```
   [Total Tickets] :=
   COUNTROWS ( FactTickets )
   ```
4. Press **Enter** or click the checkmark ✓.
5. With the measure still selected, set formatting in the ribbon:
   - Count measures (`Total Tickets`, `Backlog Count`, etc.) → **Whole number**, thousands separator on.
   - Hour measures (`MTTR Hours`, `MTTA Hours`) → **Decimal number**, 1 decimal place.
   - Display measures (`MTTR Display`, `CSAT Display`, etc.) → leave as Text (they return formatted strings).
   - Rate measures (`FCR Rate`, `SLA Compliance Rate`) → **Percentage** or **Decimal**, 1 decimal place.

Repeat for all ~30 measures in the file.

---

## 8. Build the visuals

### Page 1 — Overview

Rename the default page to "Overview" by double-clicking the tab at the bottom.

#### 8.1 KPI cards (top row)

Insert **5 Card** visuals (**+ Add visual → Card**). Drag one measure into each:

| Card label | Measure |
|---|---|
| Total Tickets | `[Total Tickets]` |
| Open Backlog | `[Backlog Count]` |
| Avg Resolution Time | `[MTTR Display]` |
| SLA Compliance | `[SLA Compliance Display]` |
| CSAT Score | `[CSAT Display]` |

**Conditional formatting — SLA Compliance card:**
- Click the card → Format visual (paint roller) → Callout value → Color → **fx**.
- Format style: Rules. Based on field: `[SLA Compliance Rate]`.
- Rule 1: ≥ 95 → green. Rule 2: 85–94.99 → orange. Rule 3: < 85 → red.

#### 8.2 Tickets over time (line chart)

- Visual: **Line chart**
- X-axis: `DimCalendar[date]`
- Y-axis: `[Total Tickets]`
- Sort: ascending by date (click the `…` menu on the visual → Sort axis → date → Ascending)

#### 8.3 Tickets by Priority (bar chart)

- Visual: **Clustered bar chart**
- Y-axis: `DimPriority[priority_name]`
- X-axis: `[Total Tickets]`
- Sort: by `[Total Tickets]` descending
- Data colors (Format → Data colors → fx → Rules on `DimPriority[priority_name]`):
  - Critical = `#D13438` (red)
  - High = `#E37D00` (orange)
  - Medium = `#0078D4` (blue)
  - Low = `#8A8886` (gray)

#### 8.4 Backlog aging (donut chart)

- Visual: **Donut chart**
- Legend: `FactTickets[ticket_age_band]`
- Values: `[Total Tickets]`
- Add a **visual-level filter**: `ticket_age_band` is not `(Resolved)`.

---

### Page 2 — SLA & Performance

Add a new page (click **+** next to page tabs at the bottom). Name it "SLA & Performance".

#### KPI cards row

| Card | Measure |
|---|---|
| SLA Breaches | `[SLA Breach Count]` |
| SLA At Risk | `[SLA At Risk]` |
| FCR Rate | `[FCR Rate Display]` |
| Oldest Open (days) | `[Oldest Open Ticket Days]` |

#### SLA breach by category (column chart)

- Visual: **Clustered column chart**
- X-axis: `DimCategory[category_name]`
- Y-axis: `[SLA Breach Rate by Category]`
- Sort: descending by Y value

#### Agent performance matrix

- Visual: **Matrix**
- Rows: `DimAgent[agent_name]`
- Values: `[Total Tickets]`, `[Agent MTTR]`, `[Agent FCR Rate]`, `[Agent SLA Compliance]`
- Sort: `[Agent SLA Compliance]` ascending (worst-performing agents at the top)
- Conditional formatting on `Agent SLA Compliance` (Format → Cell elements → Background color → fx → Rules):
  - < 80 → red
  - 80–94.99 → orange
  - ≥ 95 → green

---

### Page 3 — CSAT

Add a third page named "CSAT".

#### KPI cards

| Card | Measure |
|---|---|
| Avg CSAT | `[CSAT Display]` |
| Satisfied (4–5) | `[CSAT Satisfied Rate]` |
| Dissatisfied (1–2) | `[CSAT Dissatisfied Rate]` |

#### CSAT by category (bar chart)

- Visual: **Clustered bar chart**
- Y-axis: `DimCategory[category_name]`
- X-axis: `[Avg CSAT]`
- Sort: ascending (lowest-rated categories at top)

---

## 9. Slicers

On **every page**, add four slicers at the top (Insert → Slicer):

| Slicer field | Display mode |
|---|---|
| `DimCalendar[date]` | **Between** → switch to **Relative date** for "last 30 days" default |
| `DimPriority[priority_name]` | Vertical list |
| `DimChannel[channel_name]` | Dropdown |
| `DimCategory[category_name]` | Dropdown |

**Sync slicers across pages:**

1. Click a slicer on Page 1.
2. In the top ribbon, click **View → Sync slicers**.
3. In the Sync slicers pane, tick both **Sync** (gear icon) and **Visible** (eye icon) for all three pages.
4. Repeat for each slicer.

---

## 10. Page navigation buttons

1. On Page 1, click **Insert → Buttons → Blank**.
2. In **Format → Button → Text**, type the page name (e.g., "SLA & Performance").
3. In **Format → Action**, turn Action on, set Type to **Page navigation**, set Destination to "SLA & Performance".
4. Copy the button (Ctrl+C), paste two more, and update the text and destination for each page.
5. Select all three buttons (Shift-click) → right-click → **Group**.
6. Copy the group and paste it onto the other two pages so navigation is consistent.

> In Power BI Service, Ctrl+click a button while in Edit mode to test the navigation.

---

## 11. Save and share the report

1. Click **File → Save** and name the report `IT Helpdesk Dashboard`.
2. The report is saved to your workspace automatically — no publish step needed
   (you are already in the service).
3. To share: click **Share** (top right) → enter a colleague's email, or copy
   the shareable link.
4. To export a static snapshot: **File → Export → Export to PDF**.

---

## Refreshing data

Because the data lives in uploaded CSV files, refreshing requires re-uploading
the CSVs after re-running the pipeline:

1. Re-run `bash scripts/run_all.sh` on your machine.
2. In your workspace, click the dataset → **Settings → Data source credentials → Edit**.
3. Re-upload the updated CSVs.

> For a portfolio project, refreshing manually is fine. Automatic scheduled
> refresh of local CSVs requires a **Personal gateway** (free to install,
> runs on your local machine).
